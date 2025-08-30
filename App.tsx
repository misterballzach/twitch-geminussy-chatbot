import React, { useState, useEffect, useRef } from 'react';
import { ConfigPanel } from './components/ConfigPanel';
import { ChatPanel } from './components/ChatPanel';
import { LoginPage } from './components/LoginPage';
import { useTwitchChat } from './hooks/useTwitchChat';
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
  const [chatInput, setChatInput] = useState('');

  const { messages, connectionStatus, connect, disconnect, sendMessage } = useTwitchChat();

  // Helper function to handle the authentication logic given a full set of credentials
  const authenticate = async (auth: { accessToken: string; clientId: string; refreshToken: string; }) => {
    const { accessToken, clientId, refreshToken } = auth;
    
    if (!accessToken || !clientId) {
      alert("Access Token and Client ID are required to log in.");
      setIsAuthenticated(false);
      return;
    }

    const user = await fetchTwitchUser(accessToken, clientId);
    
    if (user) {
      setSettings(prev => ({
        ...prev,
        channel: user.login,
        username: user.login,
        oauth: accessToken, // Store the raw token
        clientId: clientId,
      }));
      setIsAuthenticated(true);
      localStorage.setItem('twitch_access_token', accessToken);
      localStorage.setItem('twitch_client_id', clientId);
      localStorage.setItem('twitch_refresh_token', refreshToken);
    } else {
      alert("Login failed. The provided token or client ID might be invalid. Please generate new credentials and try again.");
      localStorage.removeItem('twitch_access_token');
      localStorage.removeItem('twitch_client_id');
      localStorage.removeItem('twitch_refresh_token');
      localStorage.removeItem('twitch_oauth_token');
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
    disconnect();
    localStorage.removeItem('twitch_access_token');
    localStorage.removeItem('twitch_client_id');
    localStorage.removeItem('twitch_refresh_token');
    localStorage.removeItem('twitch_oauth_token');
    setSettings({ channel: '', username: '', oauth: '', clientId: '' });
    setIsAuthenticated(false);
  };

  const handleChannelChange = (newChannel: string) => {
    const sanitizedChannel = newChannel.toLowerCase().replace(/[^a-z0-9_]/g, '');
    setSettings(prev => ({ ...prev, channel: sanitizedChannel }));
  };

  const handleChatInputSend = () => {
    if (chatInput.trim() && connectionStatus === ConnectionStatus.CONNECTED) {
      sendMessage(chatInput.trim());
      setChatInput(''); // Clear input after sending
    }
  };

  if (!isAuthenticated) {
    return <LoginPage onAuthSubmit={handleAuthSubmit} />;
  }

  return (
    <div className="min-h-screen bg-zinc-900 text-gray-200 flex flex-col p-4 sm:p-6 lg:p-8">
      <header className="mb-6">
        <h1 className="text-4xl font-bold text-violet-400">Twitch Chat Client</h1>
        <p className="text-zinc-400 mt-1">Connected as <span className="font-semibold text-violet-300">{settings.username}</span></p>
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
          />
        </div>

        <div className="lg:col-span-3">
          <ChatPanel
            messages={messages}
            chatInput={chatInput}
            setChatInput={setChatInput}
            onSendMessage={handleChatInputSend}
            isDisabled={connectionStatus !== ConnectionStatus.CONNECTED}
            username={settings.username}
          />
        </div>
      </div>
    </div>
  );
};

export default App;