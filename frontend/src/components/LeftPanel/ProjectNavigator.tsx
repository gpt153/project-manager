import React, { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { Project } from '@/types/project';

interface ProjectNavigatorProps {
  onProjectSelect: (projectId: string) => void;
}

export const ProjectNavigator: React.FC<ProjectNavigatorProps> = ({ onProjectSelect }) => {
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
            <div onClick={() => toggleProject(project.id)}>
              {expandedProjects.has(project.id) ? '▼' : '▶'} {project.name}
            </div>
            {expandedProjects.has(project.id) && (
              <ul className="issue-list">
                <li>Open Issues ({project.open_issues_count || 0})</li>
                <li>Closed Issues ({project.closed_issues_count || 0})</li>
                <li>Documents</li>
              </ul>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};
