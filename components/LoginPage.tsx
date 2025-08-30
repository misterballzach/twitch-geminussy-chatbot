import React, { useState } from 'react';
import { BotIcon, PowerIcon, ClipboardIcon } from './icons/Icons';
import { getTwitchAuthUrl } from '../services/twitchAuth';

interface LoginPageProps {
  onTokenSubmit: (token: string) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onTokenSubmit }) => {
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const authUrl = getTwitchAuthUrl();

  const handleSubmit = () => {
    setError('');
    const trimmedToken = token.trim();
    if (!trimmedToken) {
      setError('Please paste your access token.');
      return;
    }
    // Basic validation: Twitch OAuth tokens are typically 30 characters long and alphanumeric.
    // This is not a foolproof check but can catch obvious mistakes.
    if (trimmedToken.length !== 30 || !/^[a-zA-Z0-9]+$/.test(trimmedToken)) {
      setError('This does not look like a valid Twitch access token. Please copy it carefully.');
      return;
    }
    onTokenSubmit(trimmedToken);
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
            <h2 className="text-xl font-semibold flex items-center gap-2"><span className="bg-violet-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">1</span> Generate Access Token</h2>
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
             <h2 className="text-xl font-semibold flex items-center gap-2"><span className="bg-violet-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">2</span> Copy the Access Token</h2>
             <p className="text-zinc-400 text-sm mt-2 ml-8">
                On the token generator page, ensure the correct scopes are selected (<code className="bg-zinc-700 px-1 rounded">chat:read</code> and <code className="bg-zinc-700 px-1 rounded">chat:edit</code> should be included). Click "Generate Token!", then copy the <strong>Access Token</strong> from the resulting page.
             </p>
          </div>
          
          <div>
            <h2 className="text-xl font-semibold flex items-center gap-2"><span className="bg-violet-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">3</span> Paste Token and Login</h2>
            <p className="text-zinc-400 text-sm mt-2 ml-8">Paste the Access Token (not the full URL) into the box below and click "Login".</p>
            <div className="mt-3 ml-8 flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Paste your 30-character access token here..."
                className="w-full flex-grow bg-zinc-700 border-zinc-600 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
                aria-label="Paste Twitch Access Token"
              />
              <button
                onClick={handleSubmit}
                className="inline-flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-md transition-colors"
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