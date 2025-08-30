import React, { useEffect, useRef } from 'react';
import type { ChatMessage as ChatMessageType } from '../types';
import { MessageSquareIcon, SendIcon } from './icons/Icons';

interface ChatPanelProps {
  messages: ChatMessageType[];
  chatInput: string;
  setChatInput: (value: string) => void;
  onSendMessage: () => void;
  isDisabled: boolean;
  username: string;
}

const ChatMessage: React.FC<{ msg: ChatMessageType }> = ({ msg }) => {
  if (msg.user === 'System') {
    return (
      <div className="px-4 py-2 text-sm text-zinc-400 italic">
        {msg.message}
      </div>
    );
  }

  return (
    <div className={`px-4 py-2 text-sm flex items-start gap-3 ${msg.isBot ? 'bg-violet-900/20' : ''}`}>
        <div className="text-zinc-400 text-right w-16 flex-shrink-0 mt-0.5">{msg.timestamp}</div>
        <div className="font-bold" style={{ color: msg.isBot ? '#a78bfa' : msg.color }}>{msg.user}{msg.isBot && ' (AI)'}:</div>
        <div className="break-words min-w-0 flex-1">{msg.message}</div>
    </div>
  );
};


export const ChatPanel: React.FC<ChatPanelProps> = ({ messages, chatInput, setChatInput, onSendMessage, isDisabled, username }) => {
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSendMessage();
    }
  };

  return (
    <div className="bg-zinc-800/50 h-[75vh] lg:h-full flex flex-col rounded-lg border border-zinc-700 backdrop-blur-sm">
      <h2 className="text-xl font-semibold text-violet-300 p-4 border-b border-zinc-700 flex items-center gap-2"><MessageSquareIcon/> Live Chat</h2>
      <div className="flex-grow overflow-y-auto p-2">
        {messages.map((msg, index) => (
          <ChatMessage key={index} msg={msg} />
        ))}
        <div ref={chatEndRef} />
      </div>
      <div className="p-4 border-t border-zinc-700">
        <div className="flex items-start gap-3">
          <textarea
            ref={inputRef}
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
            className="w-full flex-grow bg-zinc-700 border-zinc-600 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-violet-500 focus:border-violet-500 disabled:opacity-50 disabled:cursor-not-allowed"
            placeholder={isDisabled ? "Connect the bot to start chatting..." : `Chatting as ${username}...`}
            disabled={isDisabled}
          />
          <button
            onClick={onSendMessage}
            disabled={isDisabled || !chatInput.trim()}
            className="h-full bg-violet-600 hover:bg-violet-700 text-white font-bold p-3 rounded-md flex items-center justify-center gap-2 transition-colors disabled:bg-violet-800 disabled:cursor-not-allowed"
            aria-label="Send Message"
          >
            <SendIcon className="w-5 h-5"/>
          </button>
        </div>
      </div>
    </div>
  );
};