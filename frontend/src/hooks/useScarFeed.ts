import { useEffect, useState } from 'react';

export interface ScarActivity {
  id: string;
  timestamp: string;
  source: 'po' | 'scar' | 'claude';
  message: string;
  phase?: string;
}

export const useScarFeed = (projectId: string) => {
  const [activities, setActivities] = useState<ScarActivity[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const eventSource = new EventSource(`/api/sse/scar/${projectId}`);

    eventSource.onopen = () => {
      setIsConnected(true);
      console.log('SSE connected');
    };

    eventSource.onmessage = (event) => {
      const activity: ScarActivity = JSON.parse(event.data);
      setActivities((prev) => [...prev, activity]);
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      setIsConnected(false);
    };

    return () => {
      eventSource.close();
    };
  }, [projectId]);

  return { activities, isConnected };
};
