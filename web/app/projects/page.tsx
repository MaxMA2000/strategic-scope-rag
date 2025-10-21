'use client';

import { useEffect, useState } from 'react';
import { Plus, Trash2, FolderOpen, Calendar, FileText, Tag, X } from 'lucide-react';
import { projectsApi, Project } from '@/lib/api';
import { useStore } from '@/lib/store';
import { formatDistance } from 'date-fns';

export default function ProjectsPage() {
  const { projects, setProjects, setCurrentProject } = useStore();
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProject, setNewProject] = useState({ name: '', description: '', tags: '' });

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await projectsApi.list();
      setProjects(response.data);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const createProject = async () => {
    try {
      const tags = newProject.tags.split(',').map(t => t.trim()).filter(Boolean);
      await projectsApi.create({
        name: newProject.name,
        description: newProject.description || undefined,
        tags: tags.length > 0 ? tags : undefined,
      });
      setNewProject({ name: '', description: '', tags: '' });
      setShowCreateModal(false);
      loadProjects();
    } catch (error) {
      console.error('Failed to create project:', error);
    }
  };

  const deleteProject = async (id: string) => {
    if (!confirm('Are you sure you want to delete this project?')) return;
    try {
      await projectsApi.delete(id);
      loadProjects();
    } catch (error) {
      console.error('Failed to delete project:', error);
    }
  };

  const selectProject = (project: Project) => {
    setCurrentProject(project);
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-[#1a1b1e]">
        <div className="text-[#b5bac1]">Loading projects...</div>
      </div>
    );
  }

  return (
    <div className="h-screen overflow-y-auto bg-[#1a1b1e]">
      <div className="max-w-7xl mx-auto px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-[#f2f3f5] mb-2">Projects</h1>
            <p className="text-[#b5bac1]">Manage your consulting project collections</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-teal-500 to-green-600 text-white rounded-xl hover:from-teal-600 hover:to-green-700 transition-all font-semibold shadow-lg shadow-teal-500/20"
          >
            <Plus size={20} />
            New Project
          </button>
        </div>

        {projects.length === 0 ? (
          <div className="bg-[#2b2d31] border border-[#3f4147] rounded-2xl p-16 text-center">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-teal-500/20 to-green-600/20 flex items-center justify-center mx-auto mb-6">
              <FolderOpen size={40} className="text-[#23a55a]" />
            </div>
            <h3 className="text-2xl font-semibold text-[#f2f3f5] mb-3">No projects yet</h3>
            <p className="text-[#b5bac1] mb-8 max-w-md mx-auto">
              Create your first project to start organizing your documents and knowledge bases
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-8 py-3 bg-gradient-to-r from-teal-500 to-green-600 text-white rounded-xl hover:from-teal-600 hover:to-green-700 transition-all font-semibold"
            >
              Create Project
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <div
                key={project.id}
                className="group bg-[#2b2d31] border border-[#3f4147] rounded-2xl p-6 hover:border-[#4e5058] transition-all cursor-pointer"
                onClick={() => selectProject(project)}
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <FolderOpen className="text-white" size={24} />
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteProject(project.id);
                    }}
                    className="w-8 h-8 rounded-lg hover:bg-[#383a40] text-[#80848e] hover:text-red-400 flex items-center justify-center transition-colors"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>

                <h3 className="text-lg font-semibold text-[#f2f3f5] mb-2 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-teal-400 group-hover:to-green-500 transition-all">
                  {project.name}
                </h3>

                {project.description && (
                  <p className="text-sm text-[#b5bac1] mb-4 line-clamp-2">{project.description}</p>
                )}

                <div className="flex items-center gap-4 text-sm text-[#80848e] mb-4">
                  <div className="flex items-center gap-1">
                    <FileText size={14} />
                    <span>{project.document_count} docs</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Calendar size={14} />
                    <span>{project.chunk_count} chunks</span>
                  </div>
                </div>

                {project.tags && project.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {project.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-1 bg-[#383a40] border border-[#4e5058] text-[#b5bac1] text-xs rounded-lg flex items-center gap-1"
                      >
                        <Tag size={10} />
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                <div className="mt-4 pt-4 border-t border-[#3f4147] text-xs text-[#80848e]">
                  Created {formatDistance(new Date(project.created_at), new Date(), { addSuffix: true })}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Create Project Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-[#2b2d31] border border-[#3f4147] rounded-2xl p-8 max-w-md w-full shadow-2xl">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-[#f2f3f5]">Create New Project</h2>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="w-8 h-8 rounded-lg hover:bg-[#383a40] text-[#80848e] hover:text-[#f2f3f5] flex items-center justify-center transition-colors"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-[#f2f3f5] mb-2">
                    Project Name *
                  </label>
                  <input
                    type="text"
                    value={newProject.name}
                    onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                    className="w-full px-4 py-3 bg-[#383a40] border border-[#4e5058] rounded-xl text-[#f2f3f5] placeholder-[#80848e] focus:outline-none focus:border-[#23a55a] transition-colors"
                    placeholder="e.g., Tech Trends Analysis 2025"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#f2f3f5] mb-2">
                    Description
                  </label>
                  <textarea
                    value={newProject.description}
                    onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                    className="w-full px-4 py-3 bg-[#383a40] border border-[#4e5058] rounded-xl text-[#f2f3f5] placeholder-[#80848e] focus:outline-none focus:border-[#23a55a] transition-colors resize-none"
                    rows={3}
                    placeholder="Brief description of the project..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#f2f3f5] mb-2">
                    Tags (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={newProject.tags}
                    onChange={(e) => setNewProject({ ...newProject, tags: e.target.value })}
                    className="w-full px-4 py-3 bg-[#383a40] border border-[#4e5058] rounded-xl text-[#f2f3f5] placeholder-[#80848e] focus:outline-none focus:border-[#23a55a] transition-colors"
                    placeholder="e.g., technology, strategy, McKinsey"
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-8">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-3 bg-[#383a40] border border-[#4e5058] text-[#f2f3f5] rounded-xl hover:bg-[#404249] transition-colors font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={createProject}
                  disabled={!newProject.name}
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-teal-500 to-green-600 text-white rounded-xl hover:from-teal-600 hover:to-green-700 transition-all font-semibold disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-teal-500/20"
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
