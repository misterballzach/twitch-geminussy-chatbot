
import React, { useState } from 'react';
import { BotIcon, PowerIcon, ClipboardIcon } from './icons/Icons';
import { getTwitchAuthUrl } from '../services/twitchAuth';

interface LoginPageProps {
  onAuthSubmit: (auth: { accessToken: string; clientId: string; refreshToken: string }) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onAuthSubmit }) => {
  const [accessToken, setAccessToken] = useState('');
  const [clientId, setClientId] = useState('');
  const [refreshToken, setRefreshToken] = useState('');
  const [error, setError] = useState('');
  const authUrl = getTwitchAuthUrl();

  const handleSubmit = () => {
    setError('');
    const trimmedToken = accessToken.trim();
    const trimmedClientId = clientId.trim();
    const trimmedRefreshToken = refreshToken.trim();

    if (!trimmedToken || !trimmedClientId) {
      setError('Please provide both a Client ID and an Access Token.');
      return;
    }
    // Basic validation
    if (trimmedToken.length !== 30 || !/^[a-zA-Z0-9]+$/.test(trimmedToken)) {
      setError('The Access Token appears to be invalid. Please copy it carefully.');
      return;
    }
    if (trimmedClientId.length !== 30 || !/^[a-zA-Z0-9]+$/.test(trimmedClientId)) {
       setError('The Client ID appears to be invalid. Please copy it carefully.');
      return;
    }

    onAuthSubmit({ 
      accessToken: trimmedToken, 
      clientId: trimmedClientId, 
      refreshToken: trimmedRefreshToken 
    });
  };

  return (
    <div className="min-h-screen bg-zinc-900 text-gray-200 flex flex-col items-center justify-center p-4">
      <div className="text-center max-w-3xl w-full">
        <BotIcon className="w-20 h-20 mx-auto text-violet-400 mb-4" />
        <h1 className="text-5xl font-bold text-violet-400">Twitch Bot Login</h1>
        <p className="text-zinc-400 mt-4 text-lg">
          Securely connect your Twitch account to the bot.
        </p>

        <div className="mt-8 text-left bg-zinc-800/50 p-6 rounded-lg border border-zinc-700 space-y-6">
          
          <div>
            <h2 className="text-xl font-semibold flex items-center gap-2"><span className="bg-violet-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">1</span> Generate Credentials</h2>
            <p className="text-zinc-400 text-sm mt-2 ml-8">Click the button below to open the Twitch Token Generator in a new tab. You may need to authorize with Twitch.</p>
            <a
              href={authUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 ml-8 inline-flex items-center justify-center gap-3 bg-[#9146FF] hover:bg-[#7a3ad9] text-white font-bold py-2 px-5 rounded-md transition-colors"
            >
              <PowerIcon />
              Open Token Generator
            </a>
          </div>

          <div>
             <h2 className="text-xl font-semibold flex items-center gap-2"><span className="bg-violet-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">2</span> Copy Credentials</h2>
             <p className="text-zinc-400 text-sm mt-2 ml-8">
                On the token generator page, ensure the correct scopes are selected (<code className="bg-zinc-700 px-1 rounded">chat:read</code> and <code className="bg-zinc-700 px-1 rounded">chat:edit</code> should be included). Click "Generate Token!", then copy the <strong>Client ID</strong>, <strong>Access Token</strong>, and <strong>Refresh Token</strong> from the resulting page.
             </p>
          </div>
          
          <div>
            <h2 className="text-xl font-semibold flex items-center gap-2"><span className="bg-violet-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">3</span> Paste Credentials and Login</h2>
            <p className="text-zinc-400 text-sm mt-2 ml-8">Paste all three values into the boxes below and click "Login".</p>
            <div className="mt-3 ml-8 flex flex-col gap-4">
              <div>
                <label htmlFor="clientId" className="block text-sm font-medium text-zinc-300 mb-1">Client ID</label>
                <input
                  id="clientId"
                  type="text"
                  value={clientId}
                  onChange={(e) => setClientId(e.target.value)}
                  placeholder="Paste your Client ID here..."
                  className="w-full bg-zinc-700 border-zinc-600 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
                  aria-label="Paste Twitch Client ID"
                />
              </div>
              <div>
                <label htmlFor="accessToken" className="block text-sm font-medium text-zinc-300 mb-1">Access Token</label>
                <input
                  id="accessToken"
                  type="text"
                  value={accessToken}
                  onChange={(e) => setAccessToken(e.target.value)}
                  placeholder="Paste your 30-character access token here..."
                  className="w-full bg-zinc-700 border-zinc-600 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
                  aria-label="Paste Twitch Access Token"
                />
              </div>
              <div>
                <label htmlFor="refreshToken" className="block text-sm font-medium text-zinc-300 mb-1">Refresh Token (Optional)</label>
                <input
                  id="refreshToken"
                  type="text"
                  value={refreshToken}
                  onChange={(e) => setRefreshToken(e.target.value)}
                  placeholder="Paste your Refresh Token here..."
                  className="w-full bg-zinc-700 border-zinc-600 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
                  aria-label="Paste Twitch Refresh Token"
                />
              </div>

              <button
                onClick={handleSubmit}
                className="mt-2 inline-flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-md transition-colors"
              >
                <ClipboardIcon />
                Login
              </button>
            </div>
            {error && <p className="text-red-400 text-sm mt-2 ml-8">{error}</p>}
          </div>
        </div>
      </div>
    </div>
  );
};
