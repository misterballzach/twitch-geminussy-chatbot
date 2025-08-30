
export interface ChatMessage {
  user: string;
  message: string;
  isBot?: boolean;
  color?: string;
  timestamp?: string;
}

export enum ConnectionStatus {
  DISCONNECTED = 'DISCONNECTED',
  CONNECTING = 'CONNECTING',
  CONNECTED = 'CONNECTED',
  ERROR = 'ERROR',
}

export interface BotSettings {
  channel: string;
  username: string;
  oauth: string;
}