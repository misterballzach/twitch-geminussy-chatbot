import React from 'react';
import type { BotSettings } from '../types';
import { ConnectionStatus } from '../types';
import { BotIcon, PowerIcon, XCircleIcon, CheckCircleIcon, LoaderIcon } from './icons/Icons';

interface ConfigPanelProps {
  settings: BotSettings;
  status: ConnectionStatus;
  onConnect: () => void;
  onDisconnect: () => void;
  onLogout: () => void;
  onChannelChange: (channel: string) => void;
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

export const ConfigPanel: React.FC<ConfigPanelProps> = ({ settings, status, onConnect, onDisconnect, onLogout, onChannelChange }) => {
  const isConnected = status === ConnectionStatus.CONNECTED;
  const isConnecting = status === ConnectionStatus.CONNECTING;
  const isDisabled = isConnected || isConnecting;

  return (
    <div className="bg-zinc-800/50 p-4 rounded-lg border border-zinc-700 backdrop-blur-sm">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-violet-300 flex items-center gap-2"><BotIcon /> Configuration</h2>
        <StatusIndicator status={status} />
      </div>
      
      <div className="space-y-4">
        <div>
          <p className="text-sm text-zinc-300">Logged in as:</p>
          <p className="font-bold text-violet-300 text-lg">{settings.username}</p>
        </div>
        <div>
          <label htmlFor="channel-input" className="block text-sm font-medium text-zinc-300 mb-1">
            Channel to Join
          </label>
          <input
            id="channel-input"
            type="text"
            value={settings.channel}
            onChange={(e) => onChannelChange(e.target.value)}
            disabled={isDisabled}
            className="w-full bg-zinc-700 border-zinc-600 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-violet-500 focus:border-violet-500 disabled:opacity-50 disabled:cursor-not-allowed"
            placeholder="e.g., your_channel_name"
          />
        </div>
      </div>

      <div className="mt-6 space-y-3">
        {isConnected ? (
          <button onClick={onDisconnect} className="w-full bg-orange-600 hover:bg-orange-700 text-white font-bold py-2 px-4 rounded-md flex items-center justify-center gap-2 transition-colors">
            <XCircleIcon /> Disconnect
          </button>
        ) : (
          <button onClick={onConnect} disabled={isConnecting} className="w-full bg-violet-600 hover:bg-violet-700 text-white font-bold py-2 px-4 rounded-md flex items-center justify-center gap-2 transition-colors disabled:bg-violet-800 disabled:cursor-not-allowed">
            {isConnecting ? <><LoaderIcon className="animate-spin" /> Connecting...</> : <><PowerIcon /> Connect</>}
          </button>
        )}
        <button onClick={onLogout} className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-md flex items-center justify-center gap-2 transition-colors">
          <PowerIcon /> Logout
        </button>
      </div>
    </div>
  );
};