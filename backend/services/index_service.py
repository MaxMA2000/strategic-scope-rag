import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import meilisearch
from langchain_openai import AzureOpenAIEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from core import settings, logger
from core.models import IndexBuildResponse, SearchResponse, SearchResult, Chunk


class IndexService:
    """Hybrid indexing with Qdrant (dense) + Meilisearch (sparse)."""
    
    def __init__(self):
        self.data_root = Path(settings.data_root)
        
        # Initialize clients
        self.qdrant = QdrantClient(url=settings.qdrant_url)
        self.meili = meilisearch.Client(settings.meilisearch_url)
        
        # Initialize embeddings
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            azure_deployment=settings.azure_openai_embedding_deployment_name,
            api_version=settings.azure_openai_api_version
        )
    
    def _collection_name(self, project_id: str) -> str:
        """Get Qdrant collection name for project."""
        return f"project_{project_id}"
    
    def _index_name(self, project_id: str) -> str:
        """Get Meilisearch index name for project."""
        return f"project_{project_id}"
    
    def _chunks_file(self, project_id: str) -> Path:
        """Get chunks metadata file."""
        return self.data_root / project_id / "chunks" / "chunks.json"
    
    async def build_index(self, project_id: str, force_rebuild: bool = False) -> IndexBuildResponse:
        """Build hybrid index for project."""
        try:
            logger.info(f"Building index for project {project_id}")
            
            # Load all documents
            documents = await self._load_project_documents(project_id)
            if not documents:
                return IndexBuildResponse(ok=False, chunks=0)
            
            # Split into chunks
            chunks = await self._split_documents(project_id, documents)
            if not chunks:
                return IndexBuildResponse(ok=False, chunks=0)
            
            logger.info(f"Created {len(chunks)} chunks for project {project_id}")
            
            # Save chunks metadata
            self._save_chunks(project_id, chunks)
            
            # Build Qdrant collection
            await self._build_qdrant_index(project_id, chunks)
            
            # Build Meilisearch index
            await self._build_meili_index(project_id, chunks)
            
            logger.info(f"Index built successfully for project {project_id}: {len(chunks)} chunks")
            
            return IndexBuildResponse(ok=True, chunks=len(chunks), reused=False)
        
        except Exception as e:
            logger.error(f"Failed to build index for {project_id}: {e}", exc_info=True)
            raise
    
    async def search(self, project_id: str, query: str, k: int = 5) -> SearchResponse:
        """Hybrid search with reciprocal rank fusion."""
        try:
            # Dense search (Qdrant)
            dense_results = await self._search_qdrant(project_id, query, settings.retrieval_top_k_dense)
            
            # Sparse search (Meilisearch)
            sparse_results = await self._search_meili(project_id, query, settings.retrieval_top_k_sparse)
            
            # Reciprocal rank fusion
            fused_results = self._reciprocal_rank_fusion(dense_results, sparse_results, k=settings.retrieval_fusion_top_n)
            
            # Limit to top k
            final_results = fused_results[:k]
            
            return SearchResponse(
                ok=True,
                results=final_results,
                query=query
            )
        
        except Exception as e:
            logger.error(f"Search failed for {project_id}: {e}", exc_info=True)
            raise
    
    async def _load_project_documents(self, project_id: str) -> List[Document]:
        """Load all parsed documents for a project."""
        docs_dir = self.data_root / project_id / "documents"
        if not docs_dir.exists():
            return []
        
        all_docs = []
        for doc_dir in docs_dir.iterdir():
            if not doc_dir.is_dir():
                continue
            
            md_file = doc_dir / "output.md"
            if not md_file.exists():
                continue
            
            doc_id = doc_dir.name
            
            # Load metadata
            metadata_file = doc_dir / "metadata.json"
            metadata = {}
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text())
            
            # Load markdown content
            content = md_file.read_text(encoding="utf-8")
            
            doc = Document(
                page_content=content,
                metadata={
                    "document_id": doc_id,
                    "project_id": project_id,
                    "title": metadata.get("title", "Untitled"),
                    "source_type": metadata.get("source_type", "upload")
                }
            )
            all_docs.append(doc)
        
        logger.info(f"Loaded {len(all_docs)} documents for project {project_id}")
        return all_docs
    
    async def _split_documents(self, project_id: str, documents: List[Document]) -> List[Chunk]:
        """Split documents into chunks."""
        chunks = []
        
        # Markdown header splitter
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        
        # Character splitter for long sections
        char_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        for doc in documents:
            doc_id = doc.metadata.get("document_id")
            
            # Split by headers
            header_chunks = header_splitter.split_text(doc.page_content)
            
            # Further split long chunks
            for hchunk in header_chunks:
                text = hchunk.page_content.strip()
                if not text:
                    continue
                
                # If chunk is long, split further
                if len(text) > settings.chunk_size:
                    sub_docs = char_splitter.create_documents([text])
                    for sub_doc in sub_docs:
                        chunk_id = f"chunk_{uuid.uuid4().hex[:12]}"
                        content_hash = hashlib.md5(sub_doc.page_content.encode()).hexdigest()
                        
                        chunk = Chunk(
                            id=chunk_id,
                            doc_id=doc_id,
                            project_id=project_id,
                            text=sub_doc.page_content,
                            heading=hchunk.metadata.get("Header 1") or hchunk.metadata.get("Header 2"),
                            metadata={**doc.metadata, **hchunk.metadata},
                            content_hash=content_hash
                        )
                        chunks.append(chunk)
                else:
                    chunk_id = f"chunk_{uuid.uuid4().hex[:12]}"
                    content_hash = hashlib.md5(text.encode()).hexdigest()
                    
                    chunk = Chunk(
                        id=chunk_id,
                        doc_id=doc_id,
                        project_id=project_id,
                        text=text,
                        heading=hchunk.metadata.get("Header 1") or hchunk.metadata.get("Header 2"),
                        metadata={**doc.metadata, **hchunk.metadata},
                        content_hash=content_hash
                    )
                    chunks.append(chunk)
        
        return chunks
    
    def _save_chunks(self, project_id: str, chunks: List[Chunk]):
        """Save chunks metadata to file."""
        chunks_file = self._chunks_file(project_id)
        chunks_file.parent.mkdir(parents=True, exist_ok=True)
        
        chunks_data = [chunk.model_dump() for chunk in chunks]
        chunks_file.write_text(json.dumps(chunks_data, indent=2))
    
    def _load_chunks(self, project_id: str) -> List[Chunk]:
        """Load chunks metadata from file."""
        chunks_file = self._chunks_file(project_id)
        if not chunks_file.exists():
            return []
        
        chunks_data = json.loads(chunks_file.read_text())
        return [Chunk(**c) for c in chunks_data]
    
    async def _build_qdrant_index(self, project_id: str, chunks: List[Chunk]):
        """Build Qdrant vector index."""
        collection_name = self._collection_name(project_id)
        
        # Recreate collection
        try:
            self.qdrant.delete_collection(collection_name)
        except:
            pass
        
        self.qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )
        
        logger.info(f"Created Qdrant collection: {collection_name}")
        
        # Embed and upload chunks in batches
        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            texts = [c.text for c in batch]
            
            # Generate embeddings
            vectors = self.embeddings.embed_documents(texts)
            
            # Create points
            points = []
            for chunk, vector in zip(batch, vectors):
                point = PointStruct(
                    id=chunk.id,
                    vector=vector,
                    payload={
                        "text": chunk.text,
                        "doc_id": chunk.doc_id,
                        "project_id": chunk.project_id,
                        "heading": chunk.heading,
                        "metadata": chunk.metadata
                    }
                )
                points.append(point)
            
            # Upload batch
            self.qdrant.upsert(collection_name=collection_name, points=points)
            logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
        
        logger.info(f"Qdrant index built: {len(chunks)} vectors")
    
    async def _build_meili_index(self, project_id: str, chunks: List[Chunk]):
        """Build Meilisearch BM25 index."""
        index_name = self._index_name(project_id)
        
        # Delete and recreate index
        try:
            self.meili.delete_index(index_name)
        except:
            pass
        
        index = self.meili.create_index(index_name, {"primaryKey": "id"})
        
        # Prepare documents
        documents = []
        for chunk in chunks:
            documents.append({
                "id": chunk.id,
                "text": chunk.text,
                "doc_id": chunk.doc_id,
                "project_id": chunk.project_id,
                "heading": chunk.heading or "",
                "title": chunk.metadata.get("title", "")
            })
        
        # Upload in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            index.add_documents(batch)
        
        # Configure search settings
        index.update_searchable_attributes(["text", "heading", "title"])
        
        logger.info(f"Meilisearch index built: {len(chunks)} documents")
    
    async def _search_qdrant(self, project_id: str, query: str, k: int) -> List[SearchResult]:
        """Search Qdrant (dense)."""
        collection_name = self._collection_name(project_id)
        
        # Embed query
        query_vector = self.embeddings.embed_query(query)
        
        # Search
        results = self.qdrant.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=k
        )
        
        search_results = []
        for hit in results:
            search_results.append(SearchResult(
                text=hit.payload["text"],
                score=hit.score,
                metadata=hit.payload.get("metadata", {}),
                document_id=hit.payload.get("doc_id"),
                page=hit.payload.get("metadata", {}).get("page")
            ))
        
        return search_results
    
    async def _search_meili(self, project_id: str, query: str, k: int) -> List[SearchResult]:
        """Search Meilisearch (sparse BM25)."""
        index_name = self._index_name(project_id)
        
        try:
            index = self.meili.get_index(index_name)
            results = index.search(query, {"limit": k})
            
            search_results = []
            for i, hit in enumerate(results.get("hits", [])):
                # Meilisearch doesn't return scores directly, use rank
                score = 1.0 / (i + 1)
                search_results.append(SearchResult(
                    text=hit.get("text", ""),
                    score=score,
                    metadata={"heading": hit.get("heading"), "title": hit.get("title")},
                    document_id=hit.get("doc_id")
                ))
            
            return search_results
        except Exception as e:
            logger.warning(f"Meilisearch query failed: {e}")
            return []
    
    def _reciprocal_rank_fusion(
        self,
        dense_results: List[SearchResult],
        sparse_results: List[SearchResult],
        k: int = 30
    ) -> List[SearchResult]:
        """Reciprocal rank fusion of dense and sparse results."""
        # RRF: score(d) = sum(1 / (k + rank(d)))
        k_param = 60
        scores = {}
        all_results = {}
        
        # Add dense results
        for rank, result in enumerate(dense_results, start=1):
            key = result.text[:100]  # Use text snippet as key
            if key not in scores:
                scores[key] = 0
                all_results[key] = result
            scores[key] += 1.0 / (k_param + rank)
        
        # Add sparse results
        for rank, result in enumerate(sparse_results, start=1):
            key = result.text[:100]
            if key not in scores:
                scores[key] = 0
                all_results[key] = result
            scores[key] += 1.0 / (k_param + rank)
        
        # Sort by fused score
        sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        # Return top k
        fused_results = []
        for key in sorted_keys[:k]:
            result = all_results[key]
            result.score = scores[key]
            fused_results.append(result)
        
        logger.info(f"RRF fusion: {len(dense_results)} dense + {len(sparse_results)} sparse → {len(fused_results)} fused")
        return fused_results

