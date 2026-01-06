import React, { useState, useRef, useEffect } from 'react';
import { useScarFeed } from '@/hooks/useScarFeed';

interface ScarActivityFeedProps {
  projectId: string;
}

export const ScarActivityFeed: React.FC<ScarActivityFeedProps> = ({ projectId }) => {
  const [verbosity, setVerbosity] = useState<'low' | 'medium' | 'high'>('medium');
  const verbosityMap = { low: 1, medium: 2, high: 3 };
  const { activities, isConnected } = useScarFeed(projectId, verbosityMap[verbosity]);
  const activitiesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    activitiesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activities]);

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'po': return '#4CAF50';
      case 'scar': return '#2196F3';
      case 'claude': return '#FF9800';
      default: return '#999';
    }
  };

  return (
    <div className="scar-feed">
      <div className="feed-header">
        <h2>SCAR Activity</h2>
        <select value={verbosity} onChange={(e) => setVerbosity(e.target.value as any)}>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
        <span className={`status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '● Live' : '○ Disconnected'}
        </span>
      </div>
      <div className="activities">
        {activities.length === 0 ? (
          <div className="empty-state">No SCAR activity yet. Activity will appear here when commands are executed.</div>
        ) : (
          activities.map((activity) => {
            // Add icon based on message content
            let icon = '';
            const msg = activity.message.toLowerCase();
            if (msg.includes('bash:') || msg.includes('git ') || msg.includes('npm ') || msg.includes('python ')) {
              icon = '🔧 ';
            } else if (msg.includes('read') || msg.includes('reading')) {
              icon = '📖 ';
            } else if (msg.includes('write') || msg.includes('writing') || msg.includes('edit')) {
              icon = '✏️ ';
            } else if (msg.includes('analyz') || msg.includes('process')) {
              icon = '⚡ ';
            }

            return (
              <div key={activity.id} className="activity-item">
                <span className="source" style={{ color: getSourceColor(activity.source) }}>
                  [{activity.source}]
                </span>
                <span className="timestamp">
                  {new Date(activity.timestamp).toLocaleTimeString()}
                </span>
                <div className="message">{icon}{activity.message}</div>
                {activity.phase && <div className="phase">Phase: {activity.phase}</div>}
              </div>
            );
          })
        )}
        <div ref={activitiesEndRef} />
      </div>
    </div>
  );
};
