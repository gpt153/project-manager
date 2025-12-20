import { useEffect, useRef, useState } from 'react';
import { ChatMessage, WebSocketMessage } from '@/types/message';

export const useWebSocket = (projectId: string) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const wsUrl = `ws://localhost:8000/api/ws/chat/${projectId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const wsMessage: WebSocketMessage = JSON.parse(event.data);
      if (wsMessage.type === 'chat') {
        setMessages((prev) => [...prev, wsMessage.data as ChatMessage]);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [projectId]);

  const sendMessage = (content: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ content }));
    }
  };

  return { messages, isConnected, sendMessage };
};
