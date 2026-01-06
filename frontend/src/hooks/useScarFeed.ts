import { useEffect, useState } from 'react';

export interface ScarActivity {
  id: string;
  timestamp: string;
  source: 'po' | 'scar' | 'claude';
  message: string;
  phase?: string;
}

export const useScarFeed = (projectId: string, verbosity: number = 2) => {
  const [activities, setActivities] = useState<ScarActivity[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const eventSource = new EventSource(`/api/sse/scar/${projectId}?verbosity=${verbosity}`);

    eventSource.onopen = () => {
      setIsConnected(true);
      console.log('SSE connected');
    };

    // Listen for named 'activity' events (backend sends: event: activity)
    eventSource.addEventListener('activity', (event) => {
      const activity: ScarActivity = JSON.parse(event.data);
      setActivities((prev) => [...prev, activity]);
    });

    // Listen for heartbeat events to maintain connection
    eventSource.addEventListener('heartbeat', (event) => {
      console.log('SSE heartbeat:', event.data);
    });

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      setIsConnected(false);
    };

    return () => {
      eventSource.close();
    };
  }, [projectId, verbosity]);

  return { activities, isConnected };
};
