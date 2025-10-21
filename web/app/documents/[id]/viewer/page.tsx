'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, FileText, Eye, Code } from 'lucide-react';
import { documentsApi, Document } from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Link from 'next/link';

interface PageData {
  page_number: number;
  image_url?: string;
  markdown?: string;
  bounding_boxes?: Array<{
    x: number;
    y: number;
    width: number;
    height: number;
    text: string;
    type: string;
  }>;
}

export default function DocumentViewerPage() {
  const params = useParams();
  const documentId = params.id as string;
  
  const [document, setDocument] = useState<Document | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageData, setPageData] = useState<PageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'original' | 'overlay' | 'markdown'>('original');
  const [zoom, setZoom] = useState(100);
  const [showBoxes, setShowBoxes] = useState(true);

  useEffect(() => {
    loadDocument();
  }, [documentId]);

  useEffect(() => {
    if (document) {
      loadPage(currentPage);
    }
  }, [document, currentPage]);

  const loadDocument = async () => {
    try {
      // In a real implementation, you'd have an endpoint to get document details
      // For now, we'll simulate it
      setDocument({
        id: documentId,
        project_id: 'project-1',
        filename: 'example.pdf',
        file_size: 1024000,
        file_type: 'application/pdf',
        uploaded_at: new Date().toISOString(),
        page_count: 10,
        status: 'parsed',
      });
    } catch (error) {
      console.error('Failed to load document:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPage = async (pageNumber: number) => {
    try {
      const response = await documentsApi.getPage(documentId, pageNumber);
      setPageData(response.data);
    } catch (error) {
      console.error('Failed to load page:', error);
      // Simulate page data for demo
      setPageData({
        page_number: pageNumber,
        image_url: `https://via.placeholder.com/800x1100/e5e7eb/6b7280?text=Page+${pageNumber}`,
        markdown: `# Page ${pageNumber}\n\nThis is simulated markdown content for page ${pageNumber}.\n\n## Key Points\n\n- Point 1\n- Point 2\n- Point 3`,
        bounding_boxes: [
          {
            x: 50,
            y: 50,
            width: 700,
            height: 100,
            text: 'Title on page',
            type: 'title',
          },
          {
            x: 50,
            y: 200,
            width: 700,
            height: 300,
            text: 'Paragraph content',
            type: 'text',
          },
        ],
      });
    }
  };

  const nextPage = () => {
    if (document && currentPage < (document.page_count || 1)) {
      setCurrentPage(currentPage + 1);
    }
  };

  const prevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const zoomIn = () => setZoom(Math.min(zoom + 25, 200));
  const zoomOut = () => setZoom(Math.max(zoom - 25, 50));

  if (loading) {
    return <div className="text-center py-12">Loading document...</div>;
  }

  if (!document) {
    return <div className="text-center py-12">Document not found</div>;
  }

  return (
    <div className="max-w-full h-[calc(100vh-120px)] flex flex-col">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <div className="flex items-center gap-3">
            <Link
              href="/documents"
              className="text-gray-600 hover:text-gray-900 transition-colors"
            >
              ← Back
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">{document.filename}</h1>
          </div>
          <p className="text-gray-600 mt-1">
            Page {currentPage} of {document.page_count}
          </p>
        </div>

        {/* Controls */}
        <div className="flex gap-3">
          <div className="flex items-center gap-2 bg-white border border-gray-300 rounded-lg p-1">
            <button
              onClick={() => setViewMode('original')}
              className={`px-3 py-2 rounded flex items-center gap-2 transition-colors ${
                viewMode === 'original'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <Eye size={16} />
              Original
            </button>
            <button
              onClick={() => setViewMode('overlay')}
              className={`px-3 py-2 rounded flex items-center gap-2 transition-colors ${
                viewMode === 'overlay'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <FileText size={16} />
              Overlay
            </button>
            <button
              onClick={() => setViewMode('markdown')}
              className={`px-3 py-2 rounded flex items-center gap-2 transition-colors ${
                viewMode === 'markdown'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <Code size={16} />
              Markdown
            </button>
          </div>

          <div className="flex items-center gap-2 bg-white border border-gray-300 rounded-lg px-4">
            <button onClick={zoomOut} className="text-gray-700 hover:text-gray-900">
              <ZoomOut size={20} />
            </button>
            <span className="text-sm font-medium text-gray-700 w-12 text-center">
              {zoom}%
            </span>
            <button onClick={zoomIn} className="text-gray-700 hover:text-gray-900">
              <ZoomIn size={20} />
            </button>
          </div>

          {viewMode === 'overlay' && (
            <label className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg cursor-pointer">
              <input
                type="checkbox"
                checked={showBoxes}
                onChange={(e) => setShowBoxes(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm text-gray-700">Show Boxes</span>
            </label>
          )}
        </div>
      </div>

      {/* Viewer */}
      <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex">
        <div className="flex-1 overflow-auto p-8 flex items-center justify-center bg-gray-100">
          {viewMode === 'markdown' ? (
            <div className="max-w-4xl w-full bg-white p-12 rounded-lg shadow-sm">
              <div className="prose prose-lg max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {pageData?.markdown || 'No markdown content available'}
                </ReactMarkdown>
              </div>
            </div>
          ) : (
            <div className="relative" style={{ transform: `scale(${zoom / 100})` }}>
              {pageData?.image_url && (
                <img
                  src={pageData.image_url}
                  alt={`Page ${currentPage}`}
                  className="max-w-full h-auto shadow-lg"
                />
              )}
              
              {viewMode === 'overlay' && showBoxes && pageData?.bounding_boxes && (
                <div className="absolute inset-0">
                  {pageData.bounding_boxes.map((box, idx) => (
                    <div
                      key={idx}
                      className="absolute border-2 border-blue-500 bg-blue-500 bg-opacity-10 hover:bg-opacity-20 transition-opacity group cursor-pointer"
                      style={{
                        left: `${box.x}px`,
                        top: `${box.y}px`,
                        width: `${box.width}px`,
                        height: `${box.height}px`,
                      }}
                      title={box.text}
                    >
                      <div className="hidden group-hover:block absolute bottom-full left-0 mb-2 p-2 bg-gray-900 text-white text-xs rounded shadow-lg max-w-xs z-10">
                        <div className="font-semibold mb-1">{box.type}</div>
                        <div className="line-clamp-3">{box.text}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Sidebar with page thumbnails */}
        <div className="w-64 border-l border-gray-200 overflow-y-auto p-4">
          <h3 className="font-semibold text-gray-900 mb-4">Pages</h3>
          <div className="space-y-3">
            {Array.from({ length: document.page_count || 0 }, (_, i) => i + 1).map((page) => (
              <button
                key={page}
                onClick={() => setCurrentPage(page)}
                className={`w-full p-3 rounded-lg border-2 transition-colors text-left ${
                  page === currentPage
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-sm font-medium text-gray-900 mb-1">
                  Page {page}
                </div>
                <div className="w-full h-32 bg-gray-200 rounded flex items-center justify-center text-gray-400 text-xs">
                  Preview
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-center items-center gap-4 mt-6">
        <button
          onClick={prevPage}
          disabled={currentPage === 1}
          className="flex items-center gap-2 px-6 py-3 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronLeft size={20} />
          Previous
        </button>
        
        <div className="flex items-center gap-2">
          <input
            type="number"
            min={1}
            max={document.page_count}
            value={currentPage}
            onChange={(e) => {
              const page = parseInt(e.target.value);
              if (page >= 1 && page <= (document.page_count || 1)) {
                setCurrentPage(page);
              }
            }}
            className="w-20 px-3 py-2 border border-gray-300 rounded-lg text-center focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <span className="text-gray-600">/ {document.page_count}</span>
        </div>

        <button
          onClick={nextPage}
          disabled={currentPage === (document.page_count || 1)}
          className="flex items-center gap-2 px-6 py-3 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
          <ChevronRight size={20} />
        </button>
      </div>
    </div>
  );
}

