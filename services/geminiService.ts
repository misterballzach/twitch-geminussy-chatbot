
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
    // Take the last 15 messages for context and filter out system messages.
    let recentHistory = chatHistory.slice(-15).filter(msg => msg.user !== 'System');

    // The conversation for the model must start with a 'user' role.
    // Find the first non-bot message to start the conversation from.
    const firstUserMessageIndex = recentHistory.findIndex(msg => 
        !msg.isBot && msg.user.toLowerCase() !== botUsername.toLowerCase()
    );

    // If there are no user messages in the recent history, we can't respond.
    if (firstUserMessageIndex === -1) {
        return '';
    }

    // Slice the history to ensure it starts with a user message.
    recentHistory = recentHistory.slice(firstUserMessageIndex);
    
    // A more robust method to build a strictly alternating conversation history.
    // This prevents malformed requests that could cause the API to silently fail.
    const conversationHistory: GeminiContent[] = [];
    let expectedRole: 'user' | 'model' = 'user';

    // Iterate backwards through the recent history to build a valid, alternating sequence.
    for (const msg of [...recentHistory].reverse()) {
        const isBotMessage = msg.isBot || msg.user.toLowerCase() === botUsername.toLowerCase();
        const currentRole = isBotMessage ? 'model' : 'user';

        if (currentRole === expectedRole) {
            const messageText = isBotMessage ? msg.message : `${msg.user}: ${msg.message}`;
            conversationHistory.unshift({
                role: currentRole,
                parts: [{ text: messageText }]
            });
            // Flip the expected role for the next turn in the sequence.
            expectedRole = (currentRole === 'user') ? 'model' : 'user';
        }
    }
    
    // If, after processing, there's no history or the last message isn't from a user, do nothing.
    // This is a safeguard; the logic above should prevent this from happening.
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
