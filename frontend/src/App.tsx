import React, { useState } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { ProjectNavigator } from '@/components/LeftPanel/ProjectNavigator';
import { ChatInterface } from '@/components/MiddlePanel/ChatInterface';
import { ScarActivityFeed } from '@/components/RightPanel/ScarActivityFeed';
import './App.css';

function App() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);

  return (
    <div className="app">
      <PanelGroup direction="horizontal">
        <Panel defaultSize={20} minSize={15} maxSize={40}>
          <ProjectNavigator onProjectSelect={setSelectedProjectId} />
        </Panel>
        <PanelResizeHandle className="resize-handle" />
        <Panel defaultSize={40} minSize={30}>
          {selectedProjectId ? (
            <ChatInterface projectId={selectedProjectId} />
          ) : (
            <div className="empty-state">Select a project to start chatting</div>
          )}
        </Panel>
        <PanelResizeHandle className="resize-handle" />
        <Panel defaultSize={40} minSize={30}>
          {selectedProjectId ? (
            <ScarActivityFeed projectId={selectedProjectId} />
          ) : (
            <div className="empty-state">Select a project to view activity</div>
          )}
        </Panel>
      </PanelGroup>
    </div>
  );
}

export default App;
