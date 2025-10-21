'use client';

import { useEffect, useState } from 'react';
import { Activity, Loader2, CheckCircle, XCircle, Clock, RefreshCw } from 'lucide-react';
import { crawlApi, CrawlJob } from '@/lib/api';
import { useStore } from '@/lib/store';
import { formatDistance } from 'date-fns';

export default function JobsPage() {
  const { crawlJobs, setCrawlJobs, updateCrawlJob } = useStore();
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    loadJobs();
    
    if (autoRefresh) {
      const interval = setInterval(() => {
        loadJobs(true);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const loadJobs = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      // In a real implementation, you'd have an API endpoint to list all jobs
      // For now, we'll just show the jobs we have in the store
      // and update their status individually
      for (const job of crawlJobs) {
        if (job.status === 'running' || job.status === 'pending') {
          try {
            const response = await crawlApi.status(job.job_id);
            updateCrawlJob(job.job_id, response.data);
          } catch (error) {
            console.error(`Failed to update job ${job.job_id}:`, error);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load jobs:', error);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  const getStatusIcon = (status: CrawlJob['status']) => {
    switch (status) {
      case 'pending':
        return <Clock className="text-gray-400" size={20} />;
      case 'running':
        return <Loader2 className="text-blue-500 animate-spin" size={20} />;
      case 'completed':
        return <CheckCircle className="text-green-500" size={20} />;
      case 'failed':
        return <XCircle className="text-red-500" size={20} />;
    }
  };

  const getStatusColor = (status: CrawlJob['status']) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-100 text-gray-700';
      case 'running':
        return 'bg-blue-100 text-blue-700';
      case 'completed':
        return 'bg-green-100 text-green-700';
      case 'failed':
        return 'bg-red-100 text-red-700';
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Job Queue</h1>
          <p className="text-gray-600 mt-2">Monitor parsing, crawling, and indexing tasks</p>
        </div>
        <div className="flex gap-3">
          <label className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Auto-refresh</span>
          </label>
          <button
            onClick={() => loadJobs()}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {[
          {
            label: 'Total Jobs',
            value: crawlJobs.length,
            color: 'bg-gray-100 text-gray-700',
          },
          {
            label: 'Running',
            value: crawlJobs.filter((j) => j.status === 'running').length,
            color: 'bg-blue-100 text-blue-700',
          },
          {
            label: 'Completed',
            value: crawlJobs.filter((j) => j.status === 'completed').length,
            color: 'bg-green-100 text-green-700',
          },
          {
            label: 'Failed',
            value: crawlJobs.filter((j) => j.status === 'failed').length,
            color: 'bg-red-100 text-red-700',
          },
        ].map((stat) => (
          <div
            key={stat.label}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
          >
            <div className="text-sm text-gray-600 mb-2">{stat.label}</div>
            <div className={`text-3xl font-bold ${stat.color.split(' ')[1]}`}>
              {stat.value}
            </div>
          </div>
        ))}
      </div>

      {/* Jobs List */}
      {loading && crawlJobs.length === 0 ? (
        <div className="text-center py-12">
          <Loader2 className="mx-auto animate-spin text-gray-400 mb-4" size={48} />
          <p className="text-gray-600">Loading jobs...</p>
        </div>
      ) : crawlJobs.length === 0 ? (
        <div className="bg-white rounded-xl p-12 text-center shadow-sm border border-gray-200">
          <Activity size={48} className="mx-auto text-gray-400 mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No jobs yet</h3>
          <p className="text-gray-600">
            Jobs will appear here when you start parsing, crawling, or indexing
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {crawlJobs.map((job) => (
            <div
              key={job.job_id}
              className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-4">
                  {getStatusIcon(job.status)}
                  <div>
                    <div className="flex items-center gap-3">
                      <h3 className="font-semibold text-gray-900">Web Crawl</h3>
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(
                          job.status
                        )}`}
                      >
                        {job.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{job.start_url}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Job ID: {job.job_id}
                    </p>
                  </div>
                </div>
                <div className="text-right text-sm text-gray-500">
                  Started{' '}
                  {formatDistance(new Date(job.created_at), new Date(), {
                    addSuffix: true,
                  })}
                  {job.completed_at && (
                    <>
                      <br />
                      Completed{' '}
                      {formatDistance(new Date(job.completed_at), new Date(), {
                        addSuffix: true,
                      })}
                    </>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <div className="text-xs text-gray-500 mb-1">Pages Crawled</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {job.pages_crawled}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 mb-1">Pages Queued</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {job.pages_queued}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 mb-1">Total Found</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {job.pages_crawled + job.pages_queued}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 mb-1">Project</div>
                  <div className="text-sm font-semibold text-gray-900 truncate">
                    {job.project_id}
                  </div>
                </div>
              </div>

              {job.status === 'running' && (
                <div className="mb-4">
                  <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span>Progress</span>
                    <span>
                      {job.pages_crawled} / {job.pages_crawled + job.pages_queued}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{
                        width: `${
                          ((job.pages_crawled / (job.pages_crawled + job.pages_queued)) *
                            100) ||
                          0
                        }%`,
                      }}
                    />
                  </div>
                </div>
              )}

              {job.error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <div className="text-sm font-semibold text-red-800 mb-1">Error</div>
                  <div className="text-sm text-red-600">{job.error}</div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

