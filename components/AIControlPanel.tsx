
import React, { useState } from 'react';
import { SendIcon, WandIcon, LoaderIcon } from './icons/Icons';

interface AIControlPanelProps {
  onDirectMessage: (message: string) => void;
  onRewriteMessage: (message: string) => void;
  directAIResponse: string;
  isDirectLoading: boolean;
  isRewriteLoading: boolean;
  isDisabled: boolean;
}

export const AIControlPanel: React.FC<AIControlPanelProps> = ({
  onDirectMessage,
  onRewriteMessage,
  directAIResponse,
  isDirectLoading,
  isRewriteLoading,
  isDisabled,
}) => {
  const [directMessage, setDirectMessage] = useState('');
  const [rewriteMessage, setRewriteMessage] = useState('');

  const handleDirectSubmit = () => {
    if (directMessage.trim()) {
      onDirectMessage(directMessage.trim());
      setDirectMessage('');
    }
  };

  const handleRewriteSubmit = () => {
    if (rewriteMessage.trim()) {
      onRewriteMessage(rewriteMessage.trim());
      setRewriteMessage('');
    }
  };

  return (
    <div className="bg-zinc-800/50 p-4 rounded-lg border border-zinc-700 backdrop-blur-sm space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-violet-300 mb-3 flex items-center gap-2">
          <SendIcon /> Direct AI Chat
        </h2>
        <p className="text-xs text-zinc-400 mb-3">Ask the AI a question directly. This conversation is private and won't appear in Twitch chat.</p>
        <textarea
          value={directMessage}
          onChange={(e) => setDirectMessage(e.target.value)}
          rows={3}
          className="w-full bg-zinc-700 border-zinc-600 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
          placeholder="e.g., What are some good stream ideas for today?"
        />
        <button
          onClick={handleDirectSubmit}
          disabled={isDirectLoading}
          className="mt-2 w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md flex items-center justify-center gap-2 transition-colors disabled:bg-blue-800 disabled:cursor-not-allowed"
        >
          {isDirectLoading ? <><LoaderIcon className="animate-spin" /> Thinking...</> : <>Ask AI</>}
        </button>
        {directAIResponse && (
          <div className="mt-3 text-sm text-zinc-300 bg-zinc-700/50 p-3 rounded-md">
            <p className="font-bold text-violet-300">AI Response:</p>
            <p className="whitespace-pre-wrap">{directAIResponse}</p>
          </div>
        )}
      </div>

      <div className="border-t border-zinc-700 pt-6">
         <h2 className="text-xl font-semibold text-violet-300 mb-3 flex items-center gap-2">
          <WandIcon /> Message as AI
        </h2>
        <p className="text-xs text-zinc-400 mb-3">Type a message, and the AI will rewrite it in its personality before sending it to your Twitch chat. Requires bot to be connected.</p>
        <textarea
          value={rewriteMessage}
          onChange={(e) => setRewriteMessage(e.target.value)}
          rows={3}
          className="w-full bg-zinc-700 border-zinc-600 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
          placeholder="e.g., hey everyone, welcome to the stream"
          disabled={isDisabled}
        />
        <button
          onClick={handleRewriteSubmit}
          disabled={isDisabled || isRewriteLoading}
          className="mt-2 w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-md flex items-center justify-center gap-2 transition-colors disabled:bg-green-800 disabled:cursor-not-allowed"
        >
          {isRewriteLoading ? <><LoaderIcon className="animate-spin" /> Rewriting...</> : <>Rewrite & Send to Chat</>}
        </button>
      </div>
    </div>
  );
};
