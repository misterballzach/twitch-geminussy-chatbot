
import { GoogleGenAI } from "@google/genai";
import type { ChatMessage } from '../types';

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY as string });

export const generateBotResponse = async (
  systemPrompt: string,
  chatHistory: ChatMessage[],
  newMessage: ChatMessage,
  botUsername: string
): Promise<string> => {
  try {
    // Take the last 10 messages for context, plus the new one
    const recentMessages = chatHistory.slice(-10);
    
    const contents = `
      ${recentMessages.map(msg => `${msg.user}: ${msg.message}`).join('\n')}
      ${newMessage.user}: ${newMessage.message}
    `;

    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: contents,
      config: {
        systemInstruction: `${systemPrompt}\nYou are a Twitch chat bot. Your name is "${botUsername}". Do not prefix your response with your name.`,
        thinkingConfig: { thinkingBudget: 0 }, // For low latency
        temperature: 0.8,
        topP: 0.9,
      }
    });

    return response.text.trim();
  } catch (error) {
    console.error('Gemini API Error:', error);
    throw new Error('Failed to generate response from Gemini API.');
  }
};