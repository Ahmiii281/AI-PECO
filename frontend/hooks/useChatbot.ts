import { useCallback, useState } from 'react';
import { ChatMessage } from '../types';
import { predictionsAPI } from '../services/api';

const WELCOME_MESSAGE: ChatMessage = {
  id: 'welcome',
  sender: 'bot',
  text: "Hello! I'm your energy assistant powered by AI-PECO. Ask about your power usage, bills, forecasts, or how to save energy.",
};

export default function useChatbot() {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isLoading) return;

      const userMsg: ChatMessage = { id: `${Date.now()}`, sender: 'user', text: trimmed };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      try {
        const result = (await predictionsAPI.getSmartAnalysis(trimmed)) as {
          response?: string;
        };

        const botText = result?.response ?? 'Sorry, I could not generate a response.';
        const botMsg: ChatMessage = { id: `bot-${Date.now()}`, sender: 'bot', text: botText };
        setMessages((prev) => [...prev, botMsg]);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'An error occurred while getting a response.';
        setMessages((prev) => [
          ...prev,
          { id: `err-${Date.now()}`, sender: 'bot', text: message },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading]
  );

  return {
    messages,
    isLoading,
    sendMessage,
  };
}
