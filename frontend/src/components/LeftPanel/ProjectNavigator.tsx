import React, { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { Project } from '@/types/project';
import { DocumentViewer } from '@/components/DocumentViewer/DocumentViewer';

interface ProjectNavigatorProps {
  onProjectSelect: (projectId: string) => void;
}

export const ProjectNavigator: React.FC<ProjectNavigatorProps> = ({ onProjectSelect }) => {
  const [showDocumentViewer, setShowDocumentViewer] = useState<{
    projectId: string;
    type: 'vision' | 'plan';
  } | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const data = await api.getProjects();
        setProjects(data);
      } catch (error) {
        console.error('Failed to fetch projects:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
  }, []);

  const toggleProject = (projectId: string) => {
    setExpandedProjects((prev) => {
      const next = new Set(prev);
      if (next.has(projectId)) {
        next.delete(projectId);
      } else {
        next.add(projectId);
      }
      return next;
    });
  };

  if (loading) return <div>Loading projects...</div>;

  return (
    <div className="project-navigator">
      <div className="header">
        <h2>Projects</h2>
        <button onClick={() => {/* TODO: open create modal */}}>+</button>
      </div>
      <ul className="project-list">
        {projects.map((project) => (
          <li key={project.id}>
            <div className="project-header">
              <span className="expand-icon" onClick={() => toggleProject(project.id)}>
                {expandedProjects.has(project.id) ? '▼' : '▶'}
              </span>
              <span className="project-name" onClick={() => onProjectSelect(project.id)}>
                {project.name}
              </span>
            </div>
            {expandedProjects.has(project.id) && (
              <ul className="issue-list">
                <li>Open Issues ({project.open_issues_count || 0})</li>
                <li>Closed Issues ({project.closed_issues_count || 0})</li>
                <li className="documents-section">
                  <span>Documents</span>
                  <ul className="document-list">
                    <li
                      className="document-item"
                      onClick={() => setShowDocumentViewer({ projectId: project.id, type: 'vision' })}
                    >
                      📄 Vision Document
                    </li>
                    <li
                      className="document-item"
                      onClick={() => setShowDocumentViewer({ projectId: project.id, type: 'plan' })}
                    >
                      📋 Implementation Plan
                    </li>
                  </ul>
                </li>
              </ul>
            )}
          </li>
        ))}
      </ul>
      {showDocumentViewer && (
        <DocumentViewer
          projectId={showDocumentViewer.projectId}
          documentType={showDocumentViewer.type}
          onClose={() => setShowDocumentViewer(null)}
        />
      )}
    </div>
  );
};
