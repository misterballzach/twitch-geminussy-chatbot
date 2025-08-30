
import { useState, useRef, useCallback } from 'react';
import type { ChatMessage, BotSettings } from '../types';
import { ConnectionStatus } from '../types';

// Function to parse IRC messages from Twitch
const parseMessage = (rawMessage: string): { command: string, channel: string, user: string, message: string, color: string } | null => {
  const parts = rawMessage.split(' ');

  if (parts[0] === 'PING') {
    return { command: 'PING', channel: '', user: '', message: '', color: '' };
  }

  const userMatch = parts[0].match(/:(.*)!/);
  const user = userMatch ? userMatch[1] : '';

  const command = parts[1];
  const channel = parts[2]?.substring(1);

  if (command === 'PRIVMSG') {
    const message = parts.slice(3).join(' ').substring(1);
    const colorMatch = parts[0].match(/color=(.*?);/);
    const color = colorMatch ? colorMatch[1] : '#FFFFFF';
    return { command, channel, user, message, color };
  }

  return null;
};

// Simple hash function for user colors
const userColors = ['#FF69B4', '#00BFFF', '#ADFF2F', '#FFD700', '#FF4500', '#9370DB'];
const getUserColor = (username: string) => {
    let hash = 0;
    for (let i = 0; i < username.length; i++) {
        hash = username.charCodeAt(i) + ((hash << 5) - hash);
    }
    return userColors[Math.abs(hash % userColors.length)];
};


export const useTwitchChat = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
  const websocket = useRef<WebSocket | null>(null);
  const settingsRef = useRef<BotSettings | null>(null);
  const connectionStatusRef = useRef(connectionStatus);
  connectionStatusRef.current = connectionStatus;

  const addMessage = useCallback((newMessage: ChatMessage) => {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMessages(prev => [...prev.slice(-100), { ...newMessage, timestamp }]); // Keep last 100 messages
  }, []);

  const connect = useCallback((settings: BotSettings) => {
    if (websocket.current && websocket.current.readyState === WebSocket.OPEN) {
      return;
    }
    
    settingsRef.current = settings;
    setConnectionStatus(ConnectionStatus.CONNECTING);
    setMessages([]);
    addMessage({ user: 'System', message: `Connecting to #${settings.channel}...`, isBot: true });

    websocket.current = new WebSocket('wss://irc-ws.chat.twitch.tv:443');

    websocket.current.onopen = () => {
      if (!websocket.current) return;
      websocket.current.send(`PASS oauth:${settings.oauth}`);
      websocket.current.send(`NICK ${settings.username}`);
      websocket.current.send(`JOIN #${settings.channel}`);
      setConnectionStatus(ConnectionStatus.CONNECTED);
      addMessage({ user: 'System', message: `Connected to #${settings.channel}!`, isBot: true });
    };

    websocket.current.onmessage = (event) => {
      const rawMessage = event.data;
      const parsed = parseMessage(rawMessage);

      if (parsed) {
        if (parsed.command === 'PING') {
          websocket.current?.send('PONG :tmi.twitch.tv');
        } else if (parsed.command === 'PRIVMSG') {
          const newMessage: ChatMessage = {
            user: parsed.user,
            message: parsed.message,
            color: parsed.color === '#FFFFFF' ? getUserColor(parsed.user) : parsed.color,
          };
          addMessage(newMessage);
        }
      }
    };

    websocket.current.onerror = () => {
      setConnectionStatus(ConnectionStatus.ERROR);
      addMessage({ user: 'System', message: 'Connection error. Check console and credentials.', isBot: true });
    };



    websocket.current.onclose = () => {
      if (connectionStatusRef.current !== ConnectionStatus.DISCONNECTED) {
        setConnectionStatus(ConnectionStatus.DISCONNECTED);
        addMessage({ user: 'System', message: 'Disconnected from Twitch chat.', isBot: true });
      }
    };
  }, [addMessage]);

  const disconnect = useCallback(() => {
    if (websocket.current) {
      websocket.current.close();
      websocket.current = null;
      setConnectionStatus(ConnectionStatus.DISCONNECTED);
    }
  }, []);

  const sendMessage = useCallback((message: string) => {
    if (websocket.current && websocket.current.readyState === WebSocket.OPEN && settingsRef.current) {
      const formattedMessage = `PRIVMSG #${settingsRef.current.channel} :${message}`;
      websocket.current.send(formattedMessage);
      addMessage({
        user: settingsRef.current.username,
        message: message,
        isBot: true
      });
    }
  }, [addMessage]);

  return { messages, connectionStatus, connect, disconnect, sendMessage, addMessage };
};
