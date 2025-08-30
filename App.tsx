
import React, { useState, useEffect, useRef } from 'react';
import { ConfigPanel } from './components/ConfigPanel';
import { ChatPanel } from './components/ChatPanel';
import { PersonalityPanel } from './components/PersonalityPanel';
import { LoginPage } from './components/LoginPage';
import { useTwitchChat } from './hooks/useTwitchChat';
import { generateBotResponse } from './services/geminiService';
import { fetchTwitchUser } from './services/twitchAuth';
import type { ChatMessage, BotSettings } from './types';
import { ConnectionStatus } from './types';

const App: React.FC = () => {
  const [settings, setSettings] = useState<BotSettings>({
    channel: '',
    username: '',
    oauth: '',
    clientId: '',
  });
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState<string>(
    'You are a helpful and friendly Twitch chat bot named GeminiBot. Keep your responses concise, fun, and relevant to the chat. You can use Twitch emotes.'
  );
  const [responseFrequency, setResponseFrequency] = useState(0.2); // Default to 20%

  const isBotResponding = useRef(false);
  const { messages, connectionStatus, connect, disconnect, sendMessage, addMessage } = useTwitchChat();

  // Helper function to handle the authentication logic given a full set of credentials
  const authenticate = async (auth: { accessToken: string; clientId: string; refreshToken: string; }) => {
    const { accessToken, clientId, refreshToken } = auth;
    
    if (!accessToken || !clientId) {
      // This case should be handled by the LoginPage, but as a safeguard:
      alert("Access Token and Client ID are required to log in.");
      setIsAuthenticated(false);
      return;
    }

    const user = await fetchTwitchUser(accessToken, clientId);
    
    if (user) {
      setSettings({
        channel: user.login,
        username: user.login,
        oauth: `oauth:${accessToken}`,
        clientId: clientId,
      });
      setIsAuthenticated(true);
      localStorage.setItem('twitch_access_token', accessToken);
      localStorage.setItem('twitch_client_id', clientId);
      localStorage.setItem('twitch_refresh_token', refreshToken);
    } else {
      alert("Login failed. The provided token or client ID might be invalid. Please generate new credentials and try again.");
      // Clear all stored auth details on failure
      localStorage.removeItem('twitch_access_token');
      localStorage.removeItem('twitch_client_id');
      localStorage.removeItem('twitch_refresh_token');
      localStorage.removeItem('twitch_oauth_token'); // Clean up old token if present
      setIsAuthenticated(false);
    }
  };

  // On initial load, check if we have valid credentials in storage
  useEffect(() => {
    const checkExistingAuth = async () => {
      const accessToken = localStorage.getItem('twitch_access_token');
      const clientId = localStorage.getItem('twitch_client_id');
      const refreshToken = localStorage.getItem('twitch_refresh_token');

      if (accessToken && clientId) {
        await authenticate({ accessToken, clientId, refreshToken: refreshToken || '' });
      }
    };
    checkExistingAuth();
  }, []);
  
  const handleAuthSubmit = async (auth: { accessToken: string; clientId: string; refreshToken: string; }) => {
    await authenticate(auth);
  };


  useEffect(() => {
    const lastMessage = messages[messages.length - 1];

    // Conditions to ignore messages and prevent loops
    if (!lastMessage || lastMessage.isBot || lastMessage.user === 'System' || isBotResponding.current || connectionStatus !== ConnectionStatus.CONNECTED) {
      return;
    }
     if (lastMessage.user.toLowerCase() === settings.username.toLowerCase()) {
      return;
    }

    const triggerBotResponse = async () => {
      const messageText = lastMessage.message;
      const botUsernameLower = settings.username.toLowerCase();

      // More robust mention detection using a regular expression.
      // This checks for "@username" as a whole word, case-insensitively.
      // It avoids false positives where the username is a substring of another word.
      const mentionRegex = new RegExp(`@${botUsernameLower}\\b`, 'i');
      const mentioned = mentionRegex.test(messageText);
      
      const commandTriggered = messageText.toLowerCase().startsWith('!ai');
      
      const shouldRespond = mentioned || commandTriggered || (responseFrequency > 0 && Math.random() < responseFrequency);
    
      if (shouldRespond) {
        isBotResponding.current = true;
        try {
          let messageForAI = { ...lastMessage };
          if (commandTriggered) {
            messageForAI.message = lastMessage.message.substring('!ai'.length).trim();
            
            if (messageForAI.message === '') {
              sendMessage(`You can ask me a question after !ai. For example: !ai what is your favorite game?`);
              return; 
            }
          }

          const historyForAI = [...messages.slice(0, -1), messageForAI];
          const responseText = await generateBotResponse(systemPrompt, historyForAI, settings.username);
          
          if (responseText && responseText.trim() !== '') {
            const singleLineResponse = responseText.replace(/(\r\n|\n|\r)/gm, " ").trim();
            if (singleLineResponse) {
              sendMessage(singleLineResponse);
            }
          } else {
            sendMessage("I'm not sure how to respond to that.");
          }
        } catch (error) {
          console.error("Error in bot response logic:", error);
          addMessage({ user: 'System', message: 'An unexpected error occurred. Check console.', isBot: true });
        } finally {
          setTimeout(() => { isBotResponding.current = false; }, 3000); // 3-second cooldown
        }
      }
    };

    triggerBotResponse();
  }, [messages, settings.username, systemPrompt, sendMessage, addMessage, connectionStatus, responseFrequency]);


  const handleConnect = () => {
    if (settings.oauth && settings.clientId && settings.channel) {
      connect(settings);
    } else {
      alert("Authentication details or channel name are missing. Please fill them out and try again.");
    }
  };

  const handleDisconnect = () => {
    disconnect();
  };
  
  const handleLogout = () => {
    disconnect(); // Disconnect from chat first
    localStorage.removeItem('twitch_access_token');
    localStorage.removeItem('twitch_client_id');
    localStorage.removeItem('twitch_refresh_token');
    localStorage.removeItem('twitch_oauth_token'); // Clean up old token
    setSettings({ channel: '', username: '', oauth: '', clientId: '' });
    setIsAuthenticated(false);
  };

  const handleChannelChange = (newChannel: string) => {
    // Sanitize channel name to be valid for Twitch IRC
    const sanitizedChannel = newChannel.toLowerCase().replace(/[^a-z0-9_]/g, '');
    setSettings(prev => ({ ...prev, channel: sanitizedChannel }));
  };
  
  if (!isAuthenticated) {
    return <LoginPage onAuthSubmit={handleAuthSubmit} />;
  }

  return (
    <div className="min-h-screen bg-zinc-900 text-gray-200 flex flex-col p-4 sm:p-6 lg:p-8">
      <header className="mb-6">
        <h1 className="text-4xl font-bold text-violet-400">Twitch Chat AI Bot</h1>
        <p className="text-zinc-400 mt-1">Powered by Gemini - Connected as <span className="font-semibold text-violet-300">{settings.username}</span></p>
      </header>

      <div className="flex-grow grid grid-cols-1 lg:grid-cols-4 gap-6 h-full">
        <div className="lg:col-span-1 flex flex-col gap-6">
          <ConfigPanel 
            settings={settings}
            status={connectionStatus}
            onConnect={handleConnect}
            onDisconnect={handleDisconnect}
            onLogout={handleLogout}
            onChannelChange={handleChannelChange}
            responseFrequency={responseFrequency}
            onFrequencyChange={setResponseFrequency}
          />
          <PersonalityPanel 
            systemPrompt={systemPrompt}
            setSystemPrompt={setSystemPrompt}
            isDisabled={connectionStatus === ConnectionStatus.CONNECTED}
          />
        </div>

        <div className="lg:col-span-3">
          <ChatPanel messages={messages} />
        </div>
      </div>
    </div>
  );
};

export default App;
