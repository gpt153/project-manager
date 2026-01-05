import React, { useEffect, useState, useMemo } from 'react';
import { api } from '@/services/api';
import { Project, ProjectColor } from '@/types/project';
import { DocumentViewer } from '@/components/DocumentViewer/DocumentViewer';
import { generateProjectColor } from '@/utils/colorGenerator';

interface ProjectNavigatorProps {
  onProjectSelect: (project: Project) => void;
}

export const ProjectNavigator: React.FC<ProjectNavigatorProps> = ({ onProjectSelect }) => {
  const [showDocumentViewer, setShowDocumentViewer] = useState<{
    projectId: string;
    type: 'vision' | 'plan';
  } | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set());
  const [projectIssues, setProjectIssues] = useState<Map<string, any[]>>(new Map());
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Generate colors for each project (memoized)
  const projectColors = useMemo(() => {
    const colorMap = new Map<string, ProjectColor>();
    projects.forEach(project => {
      colorMap.set(project.id, generateProjectColor(project.id));
    });
    return colorMap;
  }, [projects]);

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

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const data = await api.getProjects();
      setProjects(data);
      // Optionally re-fetch issues for expanded projects
      const expandedIds = Array.from(expandedProjects);
      for (const projectId of expandedIds) {
        try {
          const issues = await api.getProjectIssues(projectId, 'all');
          setProjectIssues(prev => new Map(prev).set(projectId, issues));
        } catch (error) {
          console.error(`Failed to refresh issues for project ${projectId}:`, error);
        }
      }
    } catch (error) {
      console.error('Failed to refresh projects:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const toggleProject = async (projectId: string) => {
    const isExpanding = !expandedProjects.has(projectId);

    // Fetch issues when expanding (if not already fetched)
    if (isExpanding && !projectIssues.has(projectId)) {
      try {
        const issues = await api.getProjectIssues(projectId, 'all');
        setProjectIssues(prev => new Map(prev).set(projectId, issues));
      } catch (error) {
        console.error('Failed to fetch issues:', error);
        // Set empty array on error so we don't retry
        setProjectIssues(prev => new Map(prev).set(projectId, []));
      }
    }

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
        <div className="header-actions">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="refresh-button"
            title="Refresh project list"
          >
            {isRefreshing ? '↻' : '⟳'}
          </button>
          <button onClick={() => {/* TODO: open create modal */}}>+</button>
        </div>
      </div>
      <ul className="project-list">
        {projects.map((project) => {
          const color = projectColors.get(project.id);
          return (
            <li key={project.id}>
              <div
                className="project-header"
                style={{
                  backgroundColor: color?.light,
                  color: color?.text,
                }}
              >
                <span className="expand-icon" onClick={() => toggleProject(project.id)}>
                  {expandedProjects.has(project.id) ? '▼' : '▶'}
                </span>
                <span className="project-name" onClick={() => onProjectSelect(project)}>
                  {project.name}
                </span>
              </div>
            {expandedProjects.has(project.id) && (
              <ul className="issue-list">
                <li className="issue-section">
                  <div className="issue-section-header">
                    📂 Open Issues ({projectIssues.get(project.id)?.filter(i => i.state === 'open').length || 0})
                  </div>
                  {projectIssues.get(project.id)?.filter(i => i.state === 'open').slice(0, 5).map(issue => (
                    <div key={issue.number} className="issue-item">
                      <a href={issue.url} target="_blank" rel="noopener noreferrer" title={issue.title}>
                        #{issue.number}: {issue.title.length > 40 ? issue.title.substring(0, 40) + '...' : issue.title}
                      </a>
                    </div>
                  ))}
                  {(projectIssues.get(project.id)?.filter(i => i.state === 'open').length || 0) > 5 && (
                    <div className="issue-item more">
                      +{(projectIssues.get(project.id)?.filter(i => i.state === 'open').length || 0) - 5} more...
                    </div>
                  )}
                </li>
                <li className="issue-section">
                  <div className="issue-section-header">
                    ✅ Closed Issues ({projectIssues.get(project.id)?.filter(i => i.state === 'closed').length || 0})
                  </div>
                  {projectIssues.get(project.id)?.filter(i => i.state === 'closed').slice(0, 3).map(issue => (
                    <div key={issue.number} className="issue-item">
                      <a href={issue.url} target="_blank" rel="noopener noreferrer" title={issue.title}>
                        #{issue.number}: {issue.title.length > 40 ? issue.title.substring(0, 40) + '...' : issue.title}
                      </a>
                    </div>
                  ))}
                </li>
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
          );
        })}
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
