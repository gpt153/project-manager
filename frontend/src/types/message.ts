export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  sender?: string; // Optional: override display name
}

export interface WebSocketMessage {
  type: 'chat' | 'status' | 'error' | 'reset';
  data: ChatMessage | StatusUpdate | ErrorMessage | ResetConfirmation;
}

export interface StatusUpdate {
  status: 'connected' | 'disconnected' | 'reconnecting';
  message?: string;
}

export interface ErrorMessage {
  code: string;
  message: string;
}

export interface ResetConfirmation {
  success: boolean;
  message: string;
  new_topic_id: string;
}
