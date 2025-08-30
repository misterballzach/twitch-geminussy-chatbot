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
  });
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState<string>(
    'You are a helpful and friendly Twitch chat bot named GeminiBot. Keep your responses concise, fun, and relevant to the chat. You can use Twitch emotes.'
  );

  const isBotResponding = useRef(false);
  const { messages, connectionStatus, connect, disconnect, sendMessage, addMessage } = useTwitchChat();

  // Helper function to handle the authentication logic given a token
  const authenticateWithToken = async (token: string) => {
    // The token from the URL won't have a prefix. The one from localStorage might.
    const cleanToken = token.startsWith('oauth:') ? token.substring(6) : token;
    const fullTokenForIrc = token.startsWith('oauth:') ? token : `oauth:${token}`;
    
    const user = await fetchTwitchUser(cleanToken);
    
    if (user) {
      setSettings({
        channel: user.login,
        username: user.login,
        oauth: fullTokenForIrc, // Use the prefixed version for IRC
      });
      setIsAuthenticated(true);
      localStorage.setItem('twitch_oauth_token', fullTokenForIrc); // Store the prefixed version
    } else {
      alert("Login failed. The provided token might be invalid or expired. Please generate a new one and try again.");
      localStorage.removeItem('twitch_oauth_token');
      setIsAuthenticated(false);
    }
  };

  // On initial load, check if we already have a valid token in storage
  useEffect(() => {
    const checkExistingAuth = async () => {
      const token = localStorage.getItem('twitch_oauth_token');
      if (token) {
        await authenticateWithToken(token);
      }
    };
    checkExistingAuth();
  }, []);
  
  const handleTokenSubmit = async (token: string) => {
    if (token) {
      await authenticateWithToken(token);
    } else {
      // This case should ideally not be hit due to the validation in LoginPage
      alert("No token provided. Please try again.");
      setIsAuthenticated(false);
    }
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
      const messageText = lastMessage.message.toLowerCase();
      const mentioned = messageText.includes(`@${settings.username.toLowerCase()}`);
      // FIX: Make the command trigger case-insensitive.
      const commandTriggered = messageText.startsWith('!ai');
      
      // Logic to respond to mentions, a command, or a certain % of messages
      const shouldRespond = mentioned || commandTriggered || Math.random() < 0.2;
    
      if (shouldRespond) {
        isBotResponding.current = true;
        try {
          let messageForAI = { ...lastMessage };
          if (commandTriggered) {
            messageForAI.message = lastMessage.message.substring('!ai'.length).trim();
            
            // If the command is empty (e.g., just "!ai"), send a help message and exit.
            if (messageForAI.message === '') {
              sendMessage(`You can ask me a question after !ai. For example: !ai what is your favorite game?`);
              return; 
            }
          }

          // Construct the history for the AI, replacing the last message with the potentially modified version
          const historyForAI = [...messages.slice(0, -1), messageForAI];

          const responseText = await generateBotResponse(systemPrompt, historyForAI, settings.username);
          
          if (responseText && responseText.trim() !== '') {
            // Sanitize response: remove newlines that would crash the IRC connection
            const singleLineResponse = responseText.replace(/(\r\n|\n|\r)/gm, " ").trim();
            if (singleLineResponse) {
              sendMessage(singleLineResponse);
            }
          } else {
            // If the AI returns an empty or whitespace-only response, send a default message.
            sendMessage("I'm not sure how to respond to that.");
          }
        } catch (error) {
          console.error("Error in bot response logic:", error);
          // The service now handles API errors, so this is for other unexpected errors.
          addMessage({ user: 'System', message: 'An unexpected error occurred. Check console.', isBot: true });
        } finally {
          setTimeout(() => { isBotResponding.current = false; }, 3000); // 3-second cooldown
        }
      }
    };

    triggerBotResponse();
  }, [messages, settings.username, systemPrompt, sendMessage, addMessage, connectionStatus]);


  const handleConnect = () => {
    if (settings.oauth) {
      connect(settings);
    } else {
      alert("Authentication details are missing. Please try logging out and back in.");
    }
  };

  const handleDisconnect = () => {
    disconnect();
  };
  
  const handleLogout = () => {
    disconnect(); // Disconnect from chat first
    localStorage.removeItem('twitch_oauth_token');
    setSettings({ channel: '', username: '', oauth: '' });
    setIsAuthenticated(false);
  };
  
  if (!isAuthenticated) {
    return <LoginPage onTokenSubmit={handleTokenSubmit} />;
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