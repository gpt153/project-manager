import { useState } from 'react';
import { ProjectNavigator } from '@/components/LeftPanel/ProjectNavigator';
import { ChatInterface } from '@/components/MiddlePanel/ChatInterface';
import { ScarActivityFeed } from '@/components/RightPanel/ScarActivityFeed';
import { ResponsiveLayout } from '@/components/Layout/ResponsiveLayout';
import { Project, ProjectColor } from '@/types/project';
import { generateProjectColor } from '@/utils/colorGenerator';
import './App.css';

function App() {
  const [selectedProject, setSelectedProject] = useState<{
    project: Project;
    color: ProjectColor;
  } | null>(null);

  const handleProjectSelect = (project: Project) => {
    const color = generateProjectColor(project.id);
    setSelectedProject({ project, color });
  };

  return (
    <div className="app">
      <ResponsiveLayout
        leftPanel={<ProjectNavigator onProjectSelect={handleProjectSelect} />}
        middlePanel={
          selectedProject ? (
            <ChatInterface
              projectId={selectedProject.project.id}
              projectName={selectedProject.project.name}
              theme={selectedProject.color}
            />
          ) : (
            <div className="empty-state">Select a project to start chatting</div>
          )
        }
        rightPanel={
          selectedProject ? (
            <ScarActivityFeed projectId={selectedProject.project.id} />
          ) : (
            <div className="empty-state">Select a project to view activity</div>
          )
        }
      />
    </div>
  );
}

export default App;
