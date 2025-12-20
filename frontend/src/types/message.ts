export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface WebSocketMessage {
  type: 'chat' | 'status' | 'error';
  data: ChatMessage | StatusUpdate | ErrorMessage;
}

export interface StatusUpdate {
  status: 'connected' | 'disconnected' | 'reconnecting';
  message?: string;
}

export interface ErrorMessage {
  code: string;
  message: string;
}
