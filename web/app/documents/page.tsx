'use client';

import { useEffect, useState } from 'react';
import { Upload, FileText, Globe, Eye, Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';
import { documentsApi, crawlApi, indexApi, Document } from '@/lib/api';
import { useStore } from '@/lib/store';
import { formatDistance } from 'date-fns';
import { useDropzone } from 'react-dropzone';
import Link from 'next/link';

export default function DocumentsPage() {
  const { currentProject, documents, setDocuments } = useStore();
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [showCrawlModal, setShowCrawlModal] = useState(false);
  const [showIndexModal, setShowIndexModal] = useState(false);
  const [crawlUrl, setCrawlUrl] = useState('');
  const [indexing, setIndexing] = useState(false);

  useEffect(() => {
    if (currentProject) {
      loadDocuments();
    }
  }, [currentProject]);

  const loadDocuments = async () => {
    if (!currentProject) return;
    setLoading(true);
    try {
      const response = await documentsApi.list(currentProject.id);
      setDocuments(response.data);
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const onDrop = async (acceptedFiles: File[]) => {
    if (!currentProject) {
      alert('Please select a project first');
      return;
    }

    setUploading(true);
    for (const file of acceptedFiles) {
      try {
        await documentsApi.upload(currentProject.id, file);
      } catch (error) {
        console.error('Failed to upload file:', error);
      }
    }
    setUploading(false);
    loadDocuments();
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
  });

  const parseDocument = async (docId: string) => {
    try {
      await documentsApi.parse(docId);
      // Refresh documents after a delay to see status update
      setTimeout(loadDocuments, 1000);
    } catch (error) {
      console.error('Failed to parse document:', error);
    }
  };

  const startCrawl = async () => {
    if (!currentProject) return;
    try {
      await crawlApi.start(currentProject.id, crawlUrl);
      setCrawlUrl('');
      setShowCrawlModal(false);
      alert('Crawl job started! Check the Jobs page for progress.');
    } catch (error) {
      console.error('Failed to start crawl:', error);
    }
  };

  const buildIndex = async () => {
    if (!currentProject) return;
    setIndexing(true);
    try {
      await indexApi.build(currentProject.id);
      alert('Index building started! This may take a few minutes.');
      setShowIndexModal(false);
    } catch (error) {
      console.error('Failed to build index:', error);
    } finally {
      setIndexing(false);
    }
  };

  const getStatusIcon = (status: Document['status']) => {
    switch (status) {
      case 'uploaded':
        return <Clock className="text-gray-400" size={16} />;
      case 'parsing':
        return <Loader2 className="text-blue-500 animate-spin" size={16} />;
      case 'parsed':
        return <CheckCircle className="text-green-500" size={16} />;
      case 'failed':
        return <XCircle className="text-red-500" size={16} />;
    }
  };

  if (!currentProject) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <FileText size={48} className="mx-auto text-gray-400 mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">No project selected</h2>
        <p className="text-gray-600 mb-6">Please select a project from the Projects page first</p>
        <Link
          href="/projects"
          className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Go to Projects
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Documents</h1>
          <p className="text-gray-600 mt-2">
            Project: <span className="font-semibold">{currentProject.name}</span>
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowCrawlModal(true)}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Globe size={20} />
            Crawl Website
          </button>
          <button
            onClick={() => setShowIndexModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <FileText size={20} />
            Build Index
          </button>
        </div>
      </div>

      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`mb-8 border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input {...getInputProps()} />
        <Upload size={48} className="mx-auto text-gray-400 mb-4" />
        {uploading ? (
          <div>
            <Loader2 size={24} className="mx-auto text-blue-500 animate-spin mb-2" />
            <p className="text-gray-600">Uploading...</p>
          </div>
        ) : (
          <>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {isDragActive ? 'Drop files here' : 'Upload Documents'}
            </h3>
            <p className="text-gray-600">
              Drag and drop PDF files here, or click to browse
            </p>
          </>
        )}
      </div>

      {/* Documents List */}
      {loading ? (
        <div className="text-center py-12">Loading documents...</div>
      ) : documents.length === 0 ? (
        <div className="bg-white rounded-xl p-12 text-center shadow-sm border border-gray-200">
          <FileText size={48} className="mx-auto text-gray-400 mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No documents yet</h3>
          <p className="text-gray-600">Upload PDFs or crawl websites to get started</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                  Uploaded
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <FileText size={20} className="text-gray-400" />
                      <div>
                        <div className="font-medium text-gray-900">{doc.filename}</div>
                        {doc.page_count && (
                          <div className="text-sm text-gray-500">{doc.page_count} pages</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {doc.file_type}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(doc.status)}
                      <span className="text-sm text-gray-600 capitalize">{doc.status}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {formatDistance(new Date(doc.uploaded_at), new Date(), { addSuffix: true })}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      {doc.status === 'uploaded' && (
                        <button
                          onClick={() => parseDocument(doc.id)}
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                        >
                          Parse
                        </button>
                      )}
                      {doc.status === 'parsed' && (
                        <Link
                          href={`/documents/${doc.id}/viewer`}
                          className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors flex items-center gap-1"
                        >
                          <Eye size={14} />
                          View
                        </Link>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Crawl Modal */}
      {showCrawlModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-8 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Crawl Website</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Start URL *
                </label>
                <input
                  type="url"
                  value={crawlUrl}
                  onChange={(e) => setCrawlUrl(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="https://example.com"
                />
              </div>
              <p className="text-sm text-gray-600">
                The crawler will follow links from this page respecting robots.txt
              </p>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowCrawlModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={startCrawl}
                disabled={!crawlUrl}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Start Crawl
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Index Modal */}
      {showIndexModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-8 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Build Index</h2>
            <p className="text-gray-600 mb-6">
              This will create a hybrid search index (Qdrant + Meilisearch) for all parsed
              documents in this project. This process may take several minutes.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowIndexModal(false)}
                disabled={indexing}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={buildIndex}
                disabled={indexing}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {indexing && <Loader2 size={16} className="animate-spin" />}
                Build Index
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

