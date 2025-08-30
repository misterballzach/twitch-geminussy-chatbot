
import React from 'react';
import { SparklesIcon, InfoIcon } from './icons/Icons';

interface PersonalityPanelProps {
  systemPrompt: string;
  setSystemPrompt: (prompt: string) => void;
  isDisabled: boolean;
}

export const PersonalityPanel: React.FC<PersonalityPanelProps> = ({ systemPrompt, setSystemPrompt, isDisabled }) => {
  return (
    <div className="bg-zinc-800/50 p-4 rounded-lg border border-zinc-700 backdrop-blur-sm">
      <h2 className="text-xl font-semibold text-violet-300 mb-3 flex items-center gap-2">
        <SparklesIcon /> AI Personality
      </h2>
      <div className="text-xs text-zinc-400 bg-zinc-700/50 p-2 rounded-md flex items-start gap-2 mb-4">
        <InfoIcon className="w-4 h-4 mt-0.5 flex-shrink-0" />
        <span>Define how your bot should behave. This instruction is sent to the AI with every request. You must disconnect to change this.</span>
      </div>
      <textarea
        value={systemPrompt}
        onChange={(e) => setSystemPrompt(e.target.value)}
        rows={6}
        className="w-full bg-zinc-700 border-zinc-600 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-violet-500 focus:border-violet-500 disabled:opacity-50"
        placeholder="e.g., You are a snarky bot that only responds in rhymes."
        disabled={isDisabled}
      />
    </div>
  );
};
