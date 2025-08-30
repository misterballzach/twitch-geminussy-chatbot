import React from 'react';
import type { BotSettings } from '../types';
import { ConnectionStatus } from '../types';
import { InfoIcon, BotIcon, PowerIcon, XCircleIcon, CheckCircleIcon, LoaderIcon } from './icons/Icons';

interface ConfigPanelProps {
  settings: BotSettings;
  setSettings: React.Dispatch<React.SetStateAction<BotSettings>>;
  status: ConnectionStatus;
  onConnect: () => void;
  onDisconnect: () => void;
}

const StatusIndicator: React.FC<{ status: ConnectionStatus }> = ({ status }) => {
  switch (status) {
    case ConnectionStatus.CONNECTED:
      return <div className="flex items-center gap-2"><CheckCircleIcon className="w-5 h-5 text-green-400" /> <span className="text-green-400">Connected</span></div>;
    case ConnectionStatus.CONNECTING:
      return <div className="flex items-center gap-2"><LoaderIcon className="w-5 h-5 text-yellow-400 animate-spin" /> <span className="text-yellow-400">Connecting...</span></div>;
    case ConnectionStatus.ERROR:
      return <div className="flex items-center gap-2"><XCircleIcon className="w-5 h-5 text-red-400" /> <span className="text-red-400">Error</span></div>;
    default:
      return <div className="flex items-center gap-2"><PowerIcon className="w-5 h-5 text-zinc-400" /> <span className="text-zinc-400">Disconnected</span></div>;
  }
};

export const ConfigPanel: React.FC<ConfigPanelProps> = ({ settings, setSettings, status, onConnect, onDisconnect }) => {
  const isConnected = status === ConnectionStatus.CONNECTED;
  const isConnecting = status === ConnectionStatus.CONNECTING;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSettings(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  return (
    <div className="bg-zinc-800/50 p-4 rounded-lg border border-zinc-700 backdrop-blur-sm">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-violet-300 flex items-center gap-2"><BotIcon /> Configuration</h2>
        <StatusIndicator status={status} />
      </div>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1" htmlFor="channel">Twitch Channel</label>
          <input type="text" id="channel" name="channel" value={settings.channel} onChange={handleChange} placeholder="e.g., yourchannel" disabled={isConnected || isConnecting} className="w-full bg-zinc-700 border-zinc-600 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-violet-500 focus:border-violet-500 disabled:opacity-50" />
        </div>
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1" htmlFor="username">Bot Username</label>
          <input type="text" id="username" name="username" value={settings.username} onChange={handleChange} placeholder="e.g., yourbotname" disabled={isConnected || isConnecting} className="w-full bg-zinc-700 border-zinc-600 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-violet-500 focus:border-violet-500 disabled:opacity-50" />
        </div>
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1" htmlFor="oauth">OAuth Token</label>
          <input type="password" id="oauth" name="oauth" value={settings.oauth} onChange={handleChange} placeholder="Starts with 'oauth:'" disabled={isConnected || isConnecting} className="w-full bg-zinc-700 border-zinc-600 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-violet-500 focus:border-violet-500 disabled:opacity-50" />
        </div>
        <div className="text-xs text-zinc-400 bg-zinc-700/50 p-2 rounded-md flex items-start gap-2">
            <InfoIcon className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span>You need an <strong>OAuth Password Token</strong> from <a href="https://twitchapps.com/tmi/" target="_blank" rel="noopener noreferrer" className="text-violet-400 hover:underline">twitchapps.com/tmi/</a>. Do not use a refresh token. Keep it secret!</span>
        </div>
      </div>

      <div className="mt-6">
        {isConnected ? (
          <button onClick={onDisconnect} className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-md flex items-center justify-center gap-2 transition-colors">
            <PowerIcon /> Disconnect
          </button>
        ) : (
          <button onClick={onConnect} disabled={isConnecting} className="w-full bg-violet-600 hover:bg-violet-700 text-white font-bold py-2 px-4 rounded-md flex items-center justify-center gap-2 transition-colors disabled:bg-violet-800 disabled:cursor-not-allowed">
            {isConnecting ? <><LoaderIcon className="animate-spin" /> Connecting...</> : <><PowerIcon /> Connect</>}
          </button>
        )}
      </div>
    </div>
  );
};