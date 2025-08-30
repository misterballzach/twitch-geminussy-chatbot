import { GoogleGenAI } from "@google/genai";
import type { ChatMessage } from '../types';
import type { Chat } from '@google/genai';

// This interface matches the structure required by the Gemini API for conversation history
interface GeminiContent {
  role: 'user' | 'model';
  parts: { text: string }[];
}

const handleApiError = (error: unknown, context: string) => {
  console.error(`Gemini API Error (${context}):`, error);
  if (error instanceof Error) {
    console.error(`Gemini API Error details (${context}):`, error.message);
    if (error.message.includes('API key not valid')) {
      return 'Sorry, your Gemini API key is invalid. Please check it in the settings.';
    }
  }
  return 'Sorry, I had a problem thinking of a response.';
};

export const generateBotResponse = async (
  apiKey: string,
  systemPrompt: string,
  chatHistory: ChatMessage[],
  botUsername: string
): Promise<string> => {
  if (!apiKey) {
    return "API key not configured. Please set it in the configuration panel.";
  }
  const ai = new GoogleGenAI({ apiKey });

  try {
    let recentHistory = chatHistory.slice(-15).filter(msg => msg.user !== 'System');

    const firstUserMessageIndex = recentHistory.findIndex(msg => 
        !msg.isBot && msg.user.toLowerCase() !== botUsername.toLowerCase()
    );

    if (firstUserMessageIndex === -1) {
        return '';
    }
    recentHistory = recentHistory.slice(firstUserMessageIndex);
    
    const conversationForApi: GeminiContent[] = [];
    let expectedRole: 'user' | 'model' = 'user';

    for (const msg of [...recentHistory].reverse()) {
        const isBotMessage = msg.isBot || msg.user.toLowerCase() === botUsername.toLowerCase();
        const currentRole = isBotMessage ? 'model' : 'user';

        if (currentRole === expectedRole) {
            // Provide context to the AI by including the username for user messages
            const messageText = isBotMessage ? msg.message : `${msg.user}: ${msg.message}`;
            conversationForApi.unshift({
                role: currentRole,
                parts: [{ text: messageText }]
            });
            expectedRole = (currentRole === 'user') ? 'model' : 'user';
        }
    }
    
    const lastMessage = conversationForApi.pop();
    if (!lastMessage || lastMessage.role !== 'user' || !lastMessage.parts[0]?.text) {
      return '';
    }
      
    const historyForChat = conversationForApi;

    const chat: Chat = ai.chats.create({
      model: 'gemini-2.5-flash',
      history: historyForChat,
      config: {
        systemInstruction: `${systemPrompt}\nYou are a Twitch chat bot named "${botUsername}". Do not prefix your response with your name. Keep responses concise and suitable for a fast-paced chat.`,
        temperature: 0.8,
        topP: 0.9,
      }
    });

    // FIX: The sendMessage method expects an object with a 'message' property.
    const response = await chat.sendMessage({ message: lastMessage.parts[0].text });
    return response.text.trim();
  } catch (error) {
    return handleApiError(error, 'Chat Response');
  }
};

export const getDirectAIResponse = async (
  apiKey: string,
  systemPrompt: string,
  botUsername: string,
  userMessage: string
): Promise<string> => {
  if (!apiKey) {
    throw new Error("API key not configured.");
  }
  const ai = new GoogleGenAI({ apiKey });

  try {
    const chat: Chat = ai.chats.create({
      model: 'gemini-2.5-flash',
      config: {
        systemInstruction: `${systemPrompt}\nYou are currently in a private chat with the user. Your name is "${botUsername}".`,
        temperature: 0.7,
      }
    });

    // FIX: The sendMessage method expects an object with a 'message' property.
    const response = await chat.sendMessage({ message: userMessage });
    return response.text.trim();

  } catch (error) {
    console.error('Gemini API Error (Direct Chat):', error);
    throw error;
  }
};

export const rephraseAsBot = async (
  apiKey: string,
  systemPrompt: string,
  botUsername: string,
  textToRephrase: string
): Promise<string> => {
  if (!apiKey) {
    throw new Error("API key not configured.");
  }
  const ai = new GoogleGenAI({ apiKey });

  try {
    const rephraseInstruction = `Rephrase the following message in your voice for Twitch chat. Here is the message: "${textToRephrase}"`;
    
    const chat: Chat = ai.chats.create({
      model: 'gemini-2.5-flash',
      config: {
        systemInstruction: `${systemPrompt}\nYou are a Twitch chat bot named "${botUsername}". Your response should be a concise, rephrased version of the user's message, suitable for chat. Only provide the rephrased message, without any extra commentary or quotation marks.`,
        temperature: 0.8,
      }
    });

    // FIX: The sendMessage method expects an object with a 'message' property.
    const response = await chat.sendMessage({ message: rephraseInstruction });
    const responseText = response.text;

    const singleLineResponse = responseText.replace(/(\r\n|\n|\r)/gm, " ").trim();
    const finalResponse = singleLineResponse.replace(/^"|"$/g, '').trim();

    return finalResponse;
  } catch (error) {
    console.error('Gemini API Error (Rephrasing):', error);
    throw error;
  }
};