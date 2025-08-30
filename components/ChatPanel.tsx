
import React, { useEffect, useRef } from 'react';
import type { ChatMessage as ChatMessageType } from '../types';
import { MessageSquareIcon } from './icons/Icons';

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


export const ChatPanel: React.FC<{ messages: ChatMessageType[] }> = ({ messages }) => {
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="bg-zinc-800/50 h-[75vh] lg:h-full flex flex-col rounded-lg border border-zinc-700 backdrop-blur-sm">
      <h2 className="text-xl font-semibold text-violet-300 p-4 border-b border-zinc-700 flex items-center gap-2"><MessageSquareIcon/> Live Chat</h2>
      <div className="flex-grow overflow-y-auto p-2">
        {messages.map((msg, index) => (
          <ChatMessage key={index} msg={msg} />
        ))}
        <div ref={chatEndRef} />
      </div>
    </div>
  );
};
