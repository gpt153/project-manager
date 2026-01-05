import React, { useState } from 'react';
import { useBreakpoint } from '@/hooks/useBreakpoint';
import { MobileNav, MobileTab } from './MobileNav';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import './ResponsiveLayout.css';

interface ResponsiveLayoutProps {
  leftPanel: React.ReactNode;
  middlePanel: React.ReactNode;
  rightPanel: React.ReactNode;
}

export const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = ({
  leftPanel,
  middlePanel,
  rightPanel,
}) => {
  const breakpoint = useBreakpoint();
  const [activeTab, setActiveTab] = useState<MobileTab>('chat');

  // Desktop/Tablet: 3-panel layout
  if (breakpoint === 'desktop' || breakpoint === 'tablet') {
    return (
      <div className="responsive-layout desktop">
        <PanelGroup direction="horizontal">
          <Panel defaultSize={20} minSize={15} maxSize={40}>
            {leftPanel}
          </Panel>
          <PanelResizeHandle className="resize-handle" />
          <Panel defaultSize={40} minSize={30}>
            {middlePanel}
          </Panel>
          <PanelResizeHandle className="resize-handle" />
          <Panel defaultSize={40} minSize={30}>
            {rightPanel}
          </Panel>
        </PanelGroup>
      </div>
    );
  }

  // Mobile: Single panel with bottom navigation
  return (
    <div className="responsive-layout mobile">
      <div className="mobile-content">
        {activeTab === 'projects' && <div className="panel">{leftPanel}</div>}
        {activeTab === 'chat' && <div className="panel">{middlePanel}</div>}
        {activeTab === 'activity' && <div className="panel">{rightPanel}</div>}
      </div>
      <MobileNav activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  );
};
