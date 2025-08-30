import React, { useState, useEffect, useRef } from 'react';
import { ConfigPanel } from './components/ConfigPanel';
import { ChatPanel } from './components/ChatPanel';
import { PersonalityPanel } from './components/PersonalityPanel';
import { useTwitchChat } from './hooks/useTwitchChat';
import { generateBotResponse } from './services/geminiService';
import type { ChatMessage, BotSettings } from './types';
import { ConnectionStatus } from './types';

const App: React.FC = () => {
  const [settings, setSettings] = useState<BotSettings>({
    channel: '',
    username: '',
    oauth: '',
  });
  const [systemPrompt, setSystemPrompt] = useState<string>(
    'You are a helpful and friendly Twitch chat bot named GeminiBot. Keep your responses concise, fun, and relevant to the chat. You can use Twitch emotes.'
  );

  const isBotResponding = useRef(false);
  const { messages, connectionStatus, connect, disconnect, sendMessage, addMessage } = useTwitchChat();

  useEffect(() => {
    const lastMessage = messages[messages.length - 1];

    // Conditions to ignore messages and prevent loops
    if (!lastMessage || lastMessage.isBot || lastMessage.user === 'System' || isBotResponding.current) {
      return;
    }
     if (lastMessage.user.toLowerCase() === settings.username.toLowerCase()) {
      return;
    }

    const triggerBotResponse = async () => {
      const messageText = lastMessage.message.toLowerCase();
      const mentioned = messageText.includes(`@${settings.username.toLowerCase()}`);
      const commandTriggered = lastMessage.message.startsWith('!ai');
      
      // Logic to respond to mentions, a command, or a certain % of messages
      const shouldRespond = mentioned || commandTriggered || Math.random() < 0.2;
    
      if (shouldRespond) {
        isBotResponding.current = true;
        try {
          let messageForAI = { ...lastMessage };
          if (commandTriggered) {
            messageForAI.message = lastMessage.message.substring('!ai'.length).trim();
            
            // If the command is empty (e.g., just "!ai"), send a help message and exit.
            if (messageForAI.message === '') {
              sendMessage(`You can ask me a question after !ai. For example: !ai what is your favorite game?`);
              return; 
            }
          }

          const responseText = await generateBotResponse(systemPrompt, messages, messageForAI, settings.username);
          if (responseText && responseText.trim() !== '') {
            // Sanitize response: remove newlines that would crash the IRC connection
            const singleLineResponse = responseText.replace(/(\r\n|\n|\r)/gm, " ").trim();
            if (singleLineResponse) {
              sendMessage(singleLineResponse);
            }
          }
        } catch (error) {
          console.error("Error generating bot response:", error);
          addMessage({ user: 'System', message: 'Error from AI. Check console.', isBot: true });
        } finally {
          setTimeout(() => { isBotResponding.current = false; }, 3000); // 3-second cooldown
        }
      }
    };

    triggerBotResponse();
  }, [messages, settings.username, systemPrompt, sendMessage, addMessage]);


  const handleConnect = () => {
    if (settings.channel && settings.username && settings.oauth) {
      connect(settings);
    } else {
      alert("Please fill in all connection details.");
    }
  };

  const handleDisconnect = () => {
    disconnect();
  };
  
  return (
    <div className="min-h-screen bg-zinc-900 text-gray-200 flex flex-col p-4 sm:p-6 lg:p-8">
      <header className="mb-6">
        <h1 className="text-4xl font-bold text-violet-400">Twitch Chat AI Bot</h1>
        <p className="text-zinc-400 mt-1">Powered by Gemini - Connect to your chat and let the AI engage your viewers.</p>
      </header>

      <div className="flex-grow grid grid-cols-1 lg:grid-cols-4 gap-6 h-full">
        <div className="lg:col-span-1 flex flex-col gap-6">
          <ConfigPanel 
            settings={settings}
            setSettings={setSettings}
            status={connectionStatus}
            onConnect={handleConnect}
            onDisconnect={handleDisconnect}
          />
          <PersonalityPanel 
            systemPrompt={systemPrompt}
            setSystemPrompt={setSystemPrompt}
            isDisabled={connectionStatus === ConnectionStatus.CONNECTED}
          />
        </div>

        <div className="lg:col-span-3">
          <ChatPanel messages={messages} />
        </div>
      </div>
    </div>
  );
};

export default App;