import { useEffect, useRef, useState } from 'react';
import { ChatMessage, WebSocketMessage } from '@/types/message';

export const useWebSocket = (projectId: string) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Load conversation history on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        setIsLoadingHistory(true);
        const response = await fetch(`/api/projects/${projectId}/messages`);
        if (response.ok) {
          const history = await response.json();
          setMessages(history);
        }
      } catch (error) {
        console.error('Failed to load conversation history:', error);
      } finally {
        setIsLoadingHistory(false);
      }
    };

    loadHistory();
  }, [projectId]);

  // Set up WebSocket connection
  useEffect(() => {
    // Determine WebSocket URL based on environment
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/ws/chat/${projectId}`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const wsMessage: WebSocketMessage = JSON.parse(event.data);
      if (wsMessage.type === 'chat') {
        const chatMessage = wsMessage.data as ChatMessage;
        setMessages((prev) => [...prev, chatMessage]);
        // Turn off typing indicator when we receive a message
        if (chatMessage.role === 'assistant') {
          setIsTyping(false);
        }
      } else if (wsMessage.type === 'reset') {
        // Handle reset confirmation
        console.log('Context reset:', wsMessage.data);
        // Clear local messages to show fresh start
        setMessages([]);
        setIsTyping(false);
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
      // Show typing indicator when user sends a message
      setIsTyping(true);
      wsRef.current.send(JSON.stringify({ content }));
    }
  };

  const resetContext = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'reset' }));
    }
  };

  return { messages, isConnected, sendMessage, resetContext, isLoadingHistory, isTyping };
};
