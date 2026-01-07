import { useState, useCallback } from 'react';
import { ChatMessage } from '../types';

const WELCOME_MESSAGE: ChatMessage = {
  id: 'welcome',
  sender: 'bot',
  text: "Hello! I'm your energy assistant. I can help you understand your power consumption, save money on bills, and optimize your device usage.",
};

const SAVING_SUGGESTIONS = [
  'Schedule high-power devices like AC and heaters to run during off-peak hours to reduce costs.',
  'Setting your AC to 25°C with a fan uses less energy than running it at 20°C alone.',
  'Unplug devices when not in use. Standby mode still consumes 20-50 watts of power.',
  'Run washing machines and dryers in the evening when electricity rates are lower.',
  'Clean your AC filters regularly to maintain efficiency and reduce power consumption.',
];

const waitForResponse = (delay: number) => new Promise((resolve) => setTimeout(resolve, delay));

const generateAnswer = (userQuestion: string, previousMessages: ChatMessage[]): string => {
  const questionLower = userQuestion.toLowerCase();

  if (questionLower.includes('cost') || questionLower.includes('price') || questionLower.includes('bill')) {
    return [
      '### Cost Analysis',
      '- High power usage usually happens when cooling or heating devices are running.',
      '- Try to use heavy appliances at different times to avoid peak demand charges.',
      '- Check if your electricity provider has lower rates during certain hours.',
    ].join('\n');
  }

  if (questionLower.includes('device') || questionLower.includes('appliance')) {
    const userTexts = previousMessages
      .filter((m) => m.sender === 'user')
      .map((m) => m.text)
      .join(' ');
    
    const foundDevices = userTexts.match(/ac|air conditioner|refrigerator|fridge|computer|laptop|lights|heater|fan/gi);
    const deviceNames = foundDevices ? [...new Set(foundDevices)].join(', ') : 'your appliances';

    return [
      `Here are some tips for ${deviceNames}:`,
      '* Check standby power - devices using more than 30W when idle need attention.',
      '* Monitor when power spikes occur to identify which device is causing it.',
      '* Set devices to turn off automatically when not needed.',
    ].join('\n');
  }

  if (questionLower.includes('forecast') || questionLower.includes('prediction') || questionLower.includes('future')) {
    return [
      'The forecast is based on your past 24 hours of usage patterns.',
      'You typically see higher usage in the morning and evening, with lower usage during midday.',
      'If the forecast line is higher than actual usage, you are using less power than expected.',
    ].join('\n');
  }

  const randomSuggestion = SAVING_SUGGESTIONS[Math.floor(Math.random() * SAVING_SUGGESTIONS.length)];
  return `That is a great question! ${randomSuggestion}`;
};

const useChatAssistant = () => {
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [processing, setProcessing] = useState(false);

  const handleUserMessage = useCallback(
    async (userInput: string) => {
      const trimmedInput = userInput.trim();
      if (!trimmedInput || processing) {
        return;
      }

      const newUserMsg: ChatMessage = {
        id: `${Date.now()}`,
        sender: 'user',
        text: trimmedInput,
      };

      setChatHistory((oldHistory) => [...oldHistory, newUserMsg]);
      setProcessing(true);

      try {
        await waitForResponse(700);
        setChatHistory((oldHistory) => {
          const botReply = generateAnswer(trimmedInput, oldHistory);
          const newBotMsg: ChatMessage = {
            id: `${Date.now() + 1}`,
            sender: 'bot',
            text: botReply,
          };
          return [...oldHistory, newBotMsg];
        });
      } finally {
        setProcessing(false);
      }
    },
    [processing]
  );

  return {
    messages: chatHistory,
    isLoading: processing,
    sendMessage: handleUserMessage,
  };
};

export default useChatAssistant;
