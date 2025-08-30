
import { useState, useRef, useCallback } from 'react';
import type { ChatMessage, BotSettings } from '../types';
import { ConnectionStatus } from '../types';

// Function to parse IRC messages from Twitch
const parseMessage = (rawMessage: string): { command: string, channel: string, user: string, message: string, color: string } | null => {
  const parts = rawMessage.split(' ');

  if (parts[0] === 'PING') {
    return { command: 'PING', channel: '', user: '', message: '', color: '' };
  }

  const command = parts.length > 1 ? parts[1] : null;

  // Welcome message, indicates successful connection
  if (command === '001') {
    return { command: '001', channel: '', user: 'System', message: 'Successfully authenticated!', color: '' };
  }

  // Notices (e.g., login failure)
  if (command === 'NOTICE') {
    const message = parts.slice(3).join(' ').substring(1);
    return { command: 'NOTICE', channel: '', user: 'System', message: message, color: '' };
  }

  // Private messages in chat
  if (command === 'PRIVMSG') {
    const userMatch = parts[0].match(/:(.*)!/);
    const user = userMatch ? userMatch[1] : '';
    const channel = parts[2]?.substring(1);
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

  const disconnect = useCallback(() => {
    if (websocket.current) {
      websocket.current.close();
      websocket.current = null;
      setConnectionStatus(ConnectionStatus.DISCONNECTED);
    }
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

      // Sanitize oauth token: remove 'oauth:' prefix if present
      const oauthToken = settings.oauth.startsWith('oauth:')
        ? settings.oauth.substring('oauth:'.length)
        : settings.oauth;
        
      websocket.current.send(`PASS oauth:${oauthToken}`);
      websocket.current.send(`NICK ${settings.username}`);
      websocket.current.send(`JOIN #${settings.channel}`);
    };

    websocket.current.onmessage = (event) => {
      // A single event can contain multiple IRC messages
      const rawMessages = event.data.toString().split('\r\n').filter(Boolean);
      
      rawMessages.forEach(rawMessage => {
        const parsed = parseMessage(rawMessage);

        if (parsed) {
          switch (parsed.command) {
            case 'PING':
              websocket.current?.send('PONG :tmi.twitch.tv');
              break;
            case '001': // This is the success signal
              setConnectionStatus(ConnectionStatus.CONNECTED);
              addMessage({ user: 'System', message: `Connected to #${settingsRef.current?.channel}!`, isBot: true });
              addMessage({ user: 'System', message: `Tip: For best results, make sure the bot is a moderator in your channel (/mod ${settingsRef.current?.username})`, isBot: true });
              break;
            case 'PRIVMSG':
              addMessage({
                user: parsed.user,
                message: parsed.message,
                color: parsed.color === '#FFFFFF' ? getUserColor(parsed.user) : parsed.color,
              });
              break;
            case 'NOTICE':
              addMessage({ user: 'System', message: `Twitch Notice: ${parsed.message}`, isBot: true });
              if (parsed.message.toLowerCase().includes('login authentication failed')) {
                setConnectionStatus(ConnectionStatus.ERROR);
                disconnect(); // Also close the connection
              }
              break;
          }
        }
      });
    };

    websocket.current.onerror = () => {
      if (connectionStatusRef.current !== ConnectionStatus.DISCONNECTED) {
        setConnectionStatus(ConnectionStatus.ERROR);
        addMessage({ user: 'System', message: 'Connection error. Check console and credentials.', isBot: true });
      }
    };

    websocket.current.onclose = () => {
      // Only show disconnected message if we weren't already manually disconnecting or in an error state from auth failure
      if (connectionStatusRef.current !== ConnectionStatus.DISCONNECTED && connectionStatusRef.current !== ConnectionStatus.ERROR) {
        setConnectionStatus(ConnectionStatus.DISCONNECTED);
        addMessage({ user: 'System', message: 'Disconnected from Twitch chat.', isBot: true });
      }
    };
  }, [addMessage, disconnect]);

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