
import { GoogleGenAI } from "@google/genai";
import type { ChatMessage } from '../types';

// FIX: Initialize the GoogleGenAI client. The 'ai' variable was used before it was defined.
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY! });

// This interface matches the structure required by the Gemini API for conversation history
interface GeminiContent {
  role: 'user' | 'model';
  parts: { text: string }[];
}

export const generateBotResponse = async (
  systemPrompt: string,
  chatHistory: ChatMessage[],
  botUsername: string
): Promise<string> => {
  try {
    // Take the last 10 messages for context and filter out system messages.
    const recentHistory = chatHistory.slice(-10).filter(msg => msg.user !== 'System');

    if (recentHistory.length === 0) {
      return '';
    }
    
    // Gemini requires an alternating user/model conversation history.
    // We'll merge consecutive user messages into single 'user' turns to ensure this.
    const conversationHistory: GeminiContent[] = [];
    for (const msg of recentHistory) {
      const isBotMessage = msg.isBot || msg.user.toLowerCase() === botUsername.toLowerCase();
      const currentRole = isBotMessage ? 'model' : 'user';
      const lastTurn = conversationHistory[conversationHistory.length - 1];
      
      // Prefix user messages with their name for the AI's context.
      const messageText = isBotMessage ? msg.message : `${msg.user}: ${msg.message}`;

      if (lastTurn && lastTurn.role === currentRole) {
        // Merge with the last turn if the role is the same (e.g. two users chatting in a row)
        lastTurn.parts[0].text += `\n${messageText}`;
      } else {
        // Otherwise, start a new turn in the conversation
        conversationHistory.push({
          role: currentRole,
          parts: [{ text: messageText }]
        });
      }
    }
    
    // If, after processing, there's no history or the last message isn't from a user, do nothing.
    // This is a safeguard, as the main App logic should already prevent this scenario.
    const lastTurn = conversationHistory[conversationHistory.length - 1];
    if (!lastTurn || lastTurn.role !== 'user') {
      return '';
    }
      
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: conversationHistory,
      config: {
        systemInstruction: `${systemPrompt}\nYou are a Twitch chat bot named "${botUsername}". Do not prefix your response with your name. Keep responses concise and suitable for a fast-paced chat.`,
        thinkingConfig: { thinkingBudget: 0 }, // For low latency
        temperature: 0.8,
        topP: 0.9,
      }
    });

    return response.text.trim();
  } catch (error) {
    console.error('Gemini API Error:', error);
     if (error instanceof Error) {
        console.error('Gemini API Error details:', error.message);
    }
    // Return a user-friendly error message to be sent to chat
    return 'Sorry, I had a problem thinking of a response.';
  }
};