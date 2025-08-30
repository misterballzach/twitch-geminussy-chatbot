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
  
  // Use a ref to track status and prevent race conditions in async handlers
  const statusRef = useRef(connectionStatus);
  statusRef.current = connectionStatus;

  const addMessage = useCallback((newMessage: ChatMessage) => {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMessages(prev => [...prev.slice(-100), { ...newMessage, timestamp }]); // Keep last 100 messages
  }, []);

  // Centralized cleanup function
  const cleanupConnection = useCallback(() => {
    if (websocket.current) {
      // Remove handlers to prevent them from firing during cleanup
      websocket.current.onopen = null;
      websocket.current.onmessage = null;
      websocket.current.onerror = null;
      websocket.current.onclose = null;
      if (websocket.current.readyState !== WebSocket.CLOSED && websocket.current.readyState !== WebSocket.CLOSING) {
        websocket.current.close();
      }
      websocket.current = null;
    }
  }, []);

  const disconnect = useCallback((status = ConnectionStatus.DISCONNECTED, message?: string) => {
    cleanupConnection();
    
    // Only update state and add message if we weren't already disconnected
    if (statusRef.current !== ConnectionStatus.DISCONNECTED) {
      setConnectionStatus(status);
      if (message) {
        addMessage({ user: 'System', message, isBot: true });
      } else if (status === ConnectionStatus.ERROR) {
        addMessage({ user: 'System', message: 'Connection error. Check credentials.', isBot: true });
      } else {
        addMessage({ user: 'System', message: 'You have been disconnected.', isBot: true });
      }
    }
  }, [addMessage, cleanupConnection]);


  const connect = useCallback((settings: BotSettings) => {
    if (statusRef.current === ConnectionStatus.CONNECTING || statusRef.current === ConnectionStatus.CONNECTED) {
      return;
    }
    
    // Always clean up any previous connection artifacts before starting a new one.
    cleanupConnection();

    settingsRef.current = settings;
    setConnectionStatus(ConnectionStatus.CONNECTING);
    setMessages([]); // Clear messages on new connection
    addMessage({ user: 'System', message: `Connecting to #${settings.channel}...`, isBot: true });

    websocket.current = new WebSocket('wss://irc-ws.chat.twitch.tv:443');

    websocket.current.onopen = () => {
      if (!websocket.current || !settingsRef.current) return;
      const { oauth, username, channel } = settingsRef.current;
      
      addMessage({ user: 'System', message: 'Authenticating...', isBot: true });
      
      // The PASS command requires the "oauth:" prefix.
      const passToken = `oauth:${oauth}`;
      
      websocket.current.send('CAP REQ :twitch.tv/tags twitch.tv/commands twitch.tv/membership');
      websocket.current.send(`PASS ${passToken}`);
      websocket.current.send(`NICK ${username}`);
      websocket.current.send(`JOIN #${channel}`);
    };

    websocket.current.onmessage = (event) => {
      try {
        const rawMessages = event.data.toString().split('\r\n').filter(Boolean);
        
        rawMessages.forEach(rawMessage => {
          const parsed = parseMessage(rawMessage);
          if (parsed) {
            switch (parsed.command) {
              case 'PING':
                websocket.current?.send('PONG :tmi.twitch.tv');
                break;
              case '001':
                setConnectionStatus(ConnectionStatus.CONNECTED);
                addMessage({ user: 'System', message: `Successfully connected to #${settingsRef.current?.channel}!`, isBot: true });
                addMessage({ user: 'System', message: `IMPORTANT: Your account must have a VERIFIED EMAIL to send messages.`, isBot: true });
                addMessage({ user: 'System', message: `Tip: For best results, also make your account a moderator (/mod ${settingsRef.current?.username})`, isBot: true });
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
                  disconnect(ConnectionStatus.ERROR, `Authentication failed. Check your OAuth token.`);
                }
                break;
            }
          }
        });
      } catch (error) {
        console.error("Error processing Twitch message:", error);
        // Optionally, add a system message to inform the user
        addMessage({ user: 'System', message: 'An error occurred while processing chat messages.', isBot: true });
      }
    };

    websocket.current.onerror = () => {
      disconnect(ConnectionStatus.ERROR, 'A connection error occurred. Check your network or credentials.');
    };



    websocket.current.onclose = () => {
      // If the connection closes for any reason, this will handle it.
      disconnect(ConnectionStatus.DISCONNECTED, 'Connection has been closed by the server.');
    };
  }, [addMessage, disconnect, cleanupConnection]);

  const sendMessage = useCallback((message: string) => {
    // Defensive check: If the UI thinks we're connected but the socket is not open, it means we got disconnected uncleanly.
    // The onclose handler should catch this, but as a backup, we prevent sending and inform the user.
    if (statusRef.current === ConnectionStatus.CONNECTED && websocket.current?.readyState !== WebSocket.OPEN) {
       addMessage({ 
        user: 'System', 
        message: `Could not send message. Connection was lost. Please reconnect.`, 
        isBot: true 
      });
      return;
    }

    if (websocket.current?.readyState === WebSocket.OPEN && settingsRef.current) {
      const formattedMessage = `PRIVMSG #${settingsRef.current.channel} :${message}`;
      websocket.current.send(formattedMessage);
      // Add the bot's own message to the chat display immediately for better UX
      addMessage({
        user: settingsRef.current.username,
        message: message,
        isBot: true
      });
    } else {
      addMessage({ 
        user: 'System', 
        message: `Could not send message. Connection is not open.`, 
        isBot: true 
      });
    }
  }, [addMessage]);

  return { messages, connectionStatus, connect, disconnect, sendMessage, addMessage };
};