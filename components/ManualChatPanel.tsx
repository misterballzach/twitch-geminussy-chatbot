
import React, { useState } from 'react';
import { MessageCircleIcon } from './icons/Icons';

interface ManualChatPanelProps {
  onSendMessage: (message: string) => void;
  isDisabled: boolean;
}

export const ManualChatPanel: React.FC<ManualChatPanelProps> = ({
  onSendMessage,
  isDisabled,
}) => {
  const [message, setMessage] = useState('');

  const handleSubmit = () => {
    if (message.trim()) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Send message on Enter, but allow new lines with Shift+Enter
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="bg-zinc-800/50 p-4 rounded-lg border border-zinc-700 backdrop-blur-sm">
      <h2 className="text-xl font-semibold text-violet-300 mb-3 flex items-center gap-2">
        <MessageCircleIcon /> Manual Chat
      </h2>
      <p className="text-xs text-zinc-400 mb-3">Send a message directly to the channel as the bot. Requires the bot to be connected.</p>
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={3}
        className="w-full bg-zinc-700 border-zinc-600 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-violet-500 focus:border-violet-500 disabled:opacity-50 disabled:cursor-not-allowed"
        placeholder="Type your message here... (Enter to send)"
        disabled={isDisabled}
      />
      <button
        onClick={handleSubmit}
        disabled={isDisabled}
        className="mt-2 w-full bg-sky-600 hover:bg-sky-700 text-white font-bold py-2 px-4 rounded-md flex items-center justify-center gap-2 transition-colors disabled:bg-sky-800 disabled:cursor-not-allowed"
      >
        Send Message
      </button>
    </div>
  );
};
