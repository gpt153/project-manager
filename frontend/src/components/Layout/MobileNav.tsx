import React from 'react';
import './MobileNav.css';

export type MobileTab = 'projects' | 'chat' | 'activity';

interface MobileNavProps {
  activeTab: MobileTab;
  onTabChange: (tab: MobileTab) => void;
  hasUnreadActivity?: boolean;
}

export const MobileNav: React.FC<MobileNavProps> = ({
  activeTab,
  onTabChange,
  hasUnreadActivity = false,
}) => {
  return (
    <nav className="mobile-nav">
      <button
        className={`nav-tab ${activeTab === 'projects' ? 'active' : ''}`}
        onClick={() => onTabChange('projects')}
      >
        <span className="icon">📁</span>
        <span className="label">Projects</span>
      </button>
      <button
        className={`nav-tab ${activeTab === 'chat' ? 'active' : ''}`}
        onClick={() => onTabChange('chat')}
      >
        <span className="icon">💬</span>
        <span className="label">Chat</span>
      </button>
      <button
        className={`nav-tab ${activeTab === 'activity' ? 'active' : ''}`}
        onClick={() => onTabChange('activity')}
      >
        <span className="icon">📊</span>
        <span className="label">Activity</span>
        {hasUnreadActivity && <span className="badge"></span>}
      </button>
    </nav>
  );
};
