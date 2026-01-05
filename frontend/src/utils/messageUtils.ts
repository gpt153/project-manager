import { ChatMessage } from '@/types/message';

export function getMessageDisplayName(message: ChatMessage): string {
  if (message.sender) return message.sender;

  switch (message.role) {
    case 'user':
      return 'Sam';
    case 'assistant':
      return 'PM';
    case 'system':
      return 'System';
    default:
      return 'Unknown';
  }
}

export function getMessageStyle(role: string): string {
  return role === 'user' ? 'message-user' : 'message-assistant';
}
