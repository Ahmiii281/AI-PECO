import { useCallback, useState } from 'react';
import { ChatMessage } from '../types';
import { sendChatMessage } from '../services/geminiService';

const INITIAL_GREETING: ChatMessage = {
  id: 'initial',
  sender: 'bot',
  text: "Hello! I'm PECO-Bot. Ask me anything about your energy usage or for tips on how to save energy!",
};

const useChatAssistant = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_GREETING]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = useCallback(
    async (rawInput: string) => {
      const input = rawInput.trim();
      if (!input || isLoading) {
        return;
      }

      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        sender: 'user',
        text: input,
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      try {
        const botResponseText = await sendChatMessage(input);
        const botMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          text: botResponseText,
        };
        setMessages((prev) => [...prev, botMessage]);
      } catch (error) {
        console.error('Failed to get response from bot', error);
        const fallback: ChatMessage = {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          text: "Sorry, I'm having trouble connecting right now. Please try again later.",
        };
        setMessages((prev) => [...prev, fallback]);
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading]
  );

  return { messages, isLoading, sendMessage };
};

export default useChatAssistant;

