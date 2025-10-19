import hashlib
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

import fitz  # PyMuPDF
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from unstructured.partition.pdf import partition_pdf
from html2text import html2text

from core import settings, logger
from core.models import DocumentUploadResponse, DocumentStatus, DocumentSourceType


class PDFService:
    """Handle PDF/document upload, parsing, and page rendering."""
    
    def __init__(self):
        self.data_root = Path(settings.data_root)
    
    def _project_dir(self, project_id: str) -> Path:
        """Get project directory."""
        p = self.data_root / project_id
        p.mkdir(parents=True, exist_ok=True)
        return p
    
    def _doc_dir(self, project_id: str, doc_id: str) -> Path:
        """Get document directory."""
        p = self._project_dir(project_id) / "documents" / doc_id
        p.mkdir(parents=True, exist_ok=True)
        return p
    
    def _original_path(self, project_id: str, doc_id: str) -> Path:
        """Get original file path."""
        return self._doc_dir(project_id, doc_id) / "original.pdf"
    
    def _markdown_path(self, project_id: str, doc_id: str) -> Path:
        """Get markdown output path."""
        return self._doc_dir(project_id, doc_id) / "output.md"
    
    def _images_dir(self, project_id: str, doc_id: str) -> Path:
        """Get images directory."""
        p = self._doc_dir(project_id, doc_id) / "images"
        p.mkdir(parents=True, exist_ok=True)
        return p
    
    def _pages_dir(self, project_id: str, doc_id: str, page_type: str) -> Path:
        """Get pages directory (original/parsed)."""
        p = self._doc_dir(project_id, doc_id) / "pages" / page_type
        p.mkdir(parents=True, exist_ok=True)
        return p
    
    def _metadata_path(self, project_id: str, doc_id: str) -> Path:
        """Get metadata file path."""
        return self._doc_dir(project_id, doc_id) / "metadata.json"
    
    def _save_metadata(self, project_id: str, doc_id: str, metadata: Dict[str, Any]):
        """Save document metadata."""
        self._metadata_path(project_id, doc_id).write_text(json.dumps(metadata, indent=2))
    
    def _load_metadata(self, project_id: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Load document metadata."""
        path = self._metadata_path(project_id, doc_id)
        if path.exists():
            return json.loads(path.read_text())
        return None
    
    async def save_upload(self, project_id: str, filename: str, content: bytes) -> DocumentUploadResponse:
        """Save uploaded file."""
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        
        # Save original file
        original_path = self._original_path(project_id, doc_id)
        original_path.write_bytes(content)
        
        # Get page count
        pages = None
        try:
            with fitz.open(original_path) as doc:
                pages = doc.page_count
        except Exception as e:
            logger.warning(f"Could not read page count: {e}")
        
        # Save metadata
        metadata = {
            "id": doc_id,
            "project_id": project_id,
            "title": filename,
            "source_type": DocumentSourceType.UPLOAD.value,
            "status": DocumentStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "pages": pages,
            "filename": filename,
        }
        self._save_metadata(project_id, doc_id, metadata)
        
        logger.info(f"Saved upload: {doc_id} - {filename} ({pages} pages)")
        
        return DocumentUploadResponse(
            document_id=doc_id,
            project_id=project_id,
            title=filename,
            pages=pages,
            status=DocumentStatus.PENDING
        )
    
    async def list_documents(self, project_id: str) -> List[Dict[str, Any]]:
        """List all documents for a project."""
        docs_dir = self._project_dir(project_id) / "documents"
        if not docs_dir.exists():
            return []
        
        documents = []
        for doc_dir in docs_dir.iterdir():
            if doc_dir.is_dir():
                metadata = self._load_metadata(project_id, doc_dir.name)
                if metadata:
                    documents.append(metadata)
        
        return documents
    
    async def parse_document(self, project_id: str, doc_id: str, job_id: str):
        """Parse document in background."""
        try:
            logger.info(f"Starting parse job {job_id} for {doc_id}")
            
            # Update status
            metadata = self._load_metadata(project_id, doc_id)
            if not metadata:
                raise ValueError(f"Document {doc_id} not found")
            
            metadata["status"] = DocumentStatus.PARSING.value
            metadata["job_id"] = job_id
            self._save_metadata(project_id, doc_id, metadata)
            
            # Render original pages
            self._render_original_pages(project_id, doc_id)
            
            # Parse with Unstructured
            elements = self._parse_with_unstructured(project_id, doc_id)
            
            # Generate markdown
            self._generate_markdown(project_id, doc_id, elements)
            
            # Render parsed pages with boxes
            self._render_parsed_pages(project_id, doc_id, elements)
            
            # Update status
            metadata["status"] = DocumentStatus.READY.value
            metadata["parsed_at"] = datetime.utcnow().isoformat()
            self._save_metadata(project_id, doc_id, metadata)
            
            logger.info(f"Parse job {job_id} completed for {doc_id}")
        
        except Exception as e:
            logger.error(f"Parse job {job_id} failed: {e}", exc_info=True)
            metadata = self._load_metadata(project_id, doc_id)
            if metadata:
                metadata["status"] = DocumentStatus.ERROR.value
                metadata["error"] = str(e)
                self._save_metadata(project_id, doc_id, metadata)
    
    def _render_original_pages(self, project_id: str, doc_id: str, dpi: int = 144):
        """Render original PDF pages as PNG."""
        pdf_path = self._original_path(project_id, doc_id)
        out_dir = self._pages_dir(project_id, doc_id, "original")
        
        with fitz.open(pdf_path) as doc:
            page_count = doc.page_count  # Get page count before doc closes
            for idx, page in enumerate(doc, start=1):
                mat = fitz.Matrix(dpi/72, dpi/72)
                pix = page.get_pixmap(matrix=mat)
                (out_dir / f"page-{idx:04d}.png").write_bytes(pix.tobytes("png"))
        
        logger.info(f"Rendered {page_count} original pages for {doc_id}")
    
    def _parse_with_unstructured(self, project_id: str, doc_id: str) -> List[Any]:
        """Parse PDF with Unstructured."""
        pdf_path = str(self._original_path(project_id, doc_id))
        
        logger.info(f"Parsing {doc_id} with Unstructured...")
        
        elements = partition_pdf(
            filename=pdf_path,
            strategy="hi_res",
            infer_table_structure=True,
            ocr_languages="eng",  # Add chi_sim if needed
            # ocr_engine="paddleocr",  # Uncomment if PaddleOCR installed
        )
        
        logger.info(f"Extracted {len(elements)} elements from {doc_id}")
        return elements
    
    def _generate_markdown(self, project_id: str, doc_id: str, elements: List[Any]):
        """Generate Markdown from parsed elements."""
        md_lines = []
        img_dir = self._images_dir(project_id, doc_id)
        
        # Extract images from PDF
        pdf_path = self._original_path(project_id, doc_id)
        image_map = {}
        with fitz.open(pdf_path) as doc:
            for page_num, page in enumerate(doc, start=1):
                image_map[page_num] = []
                for img_index, img in enumerate(page.get_images(full=True), start=1):
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        img_path = img_dir / f"page{page_num}_img{img_index}.png"
                        if pix.n < 5:
                            pix.save(str(img_path))
                        else:
                            pix = fitz.Pixmap(fitz.csRGB, pix)
                            pix.save(str(img_path))
                        image_map[page_num].append(img_path.name)
                    except Exception as e:
                        logger.warning(f"Failed to extract image: {e}")
        
        # Convert elements to Markdown
        inserted_images = set()
        for el in elements:
            cat = getattr(el, "category", None)
            text = (getattr(el, "text", "") or "").strip()
            meta = getattr(el, "metadata", None)
            page_num = getattr(meta, "page_number", None) if meta else None
            
            if not text and cat != "Image":
                continue
            
            if cat == "Title":
                md_lines.append(f"# {text}\n")
            elif cat in ["Header", "Subheader"]:
                md_lines.append(f"## {text}\n")
            elif cat == "Table":
                html = getattr(meta, "text_as_html", None) if meta else None
                if html:
                    md_lines.append(html2text(html) + "\n")
                else:
                    md_lines.append(text + "\n")
            elif cat == "Image" and page_num:
                for img_name in image_map.get(page_num, []):
                    if (page_num, img_name) not in inserted_images:
                        md_lines.append(f"![Image](./images/{img_name})\n")
                        inserted_images.add((page_num, img_name))
            else:
                md_lines.append(text + "\n")
        
        # Save markdown
        md_path = self._markdown_path(project_id, doc_id)
        md_path.write_text("\n".join(md_lines), encoding="utf-8")
        
        logger.info(f"Generated markdown for {doc_id} ({len(md_lines)} lines)")
    
    def _render_parsed_pages(self, project_id: str, doc_id: str, elements: List[Any], dpi: int = 144):
        """Render pages with bounding boxes."""
        pdf_path = self._original_path(project_id, doc_id)
        out_dir = self._pages_dir(project_id, doc_id, "parsed")
        
        # Group elements by page
        segments_by_page = {}
        for el in elements:
            meta = getattr(el, "metadata", None)
            if not meta:
                continue
            page_num = getattr(meta, "page_number", None)
            if page_num is None:
                continue
            if page_num not in segments_by_page:
                segments_by_page[page_num] = []
            segments_by_page[page_num].append({
                "category": getattr(el, "category", "Text"),
                "coordinates": getattr(meta, "coordinates", None)
            })
        
        # Render each page
        with fitz.open(pdf_path) as doc:
            for page_num in range(1, doc.page_count + 1):
                page = doc.load_page(page_num - 1)
                mat = fitz.Matrix(dpi/72, dpi/72)
                pix = page.get_pixmap(matrix=mat)
                pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                fig, ax = plt.subplots(1, figsize=(10, 10))
                ax.imshow(pil_img)
                ax.axis("off")
                
                # Draw boxes
                segments = segments_by_page.get(page_num, [])
                self._plot_boxes(ax, pix, segments)
                
                fig.tight_layout()
                fig.savefig(out_dir / f"page-{page_num:04d}.png", bbox_inches="tight", pad_inches=0)
                plt.close(fig)
        
        logger.info(f"Rendered {doc.page_count} parsed pages for {doc_id}")
    
    def _plot_boxes(self, ax, pix, segments):
        """Plot bounding boxes on image."""
        category_colors = {
            "Title": "orchid",
            "Image": "forestgreen",
            "Table": "tomato",
        }
        
        for seg in segments:
            coords = seg.get("coordinates")
            if not coords:
                continue
            
            points = getattr(coords, "points", None)
            if not points:
                continue
            
            lw = getattr(coords, "layout_width", pix.width)
            lh = getattr(coords, "layout_height", pix.height)
            
            scaled = [(x * pix.width / lw, y * pix.height / lh) for x, y in points]
            color = category_colors.get(seg.get("category"), "deepskyblue")
            
            poly = patches.Polygon(scaled, linewidth=1, edgecolor=color, facecolor="none")
            ax.add_patch(poly)

