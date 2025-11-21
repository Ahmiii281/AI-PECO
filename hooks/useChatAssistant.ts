import { useCallback, useMemo, useState } from 'react';
import { ChatMessage } from '../types';

const INITIAL_GREETING: ChatMessage = {
  id: 'initial',
  sender: 'bot',
  text: "Hi there! I'm PECO-Bot. Ask me anything about your energy usage, billing surprises, or how to squeeze a few more watts out of your setup.",
};

const ENERGY_TIPS = [
  'Group your high-draw devices on smart schedules so they do not overlap during peak tariff windows.',
  'Fans plus a 24 °C AC setting usually feel the same as blasting 20 °C but uses ~15% less power.',
  'Idle electronics still sip power. A smart strip can cut 20‑50 W without you noticing.',
  'Try batching laundry after sunset if your utility offers off-peak rates—it is an easy win.',
  'A weekly reminder to clean AC filters keeps airflow strong and prevents runaway consumption.',
];

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const craftResponse = (prompt: string, history: ChatMessage[]): string => {
  const normalized = prompt.toLowerCase();

  if (normalized.includes('cost') || normalized.includes('bill')) {
    return [
      '### Bill Breakdown',
      `- Recent peaks usually come from cooling loads and anything above 1.5 kW.`,
      '- Spread heavy appliances across the day to keep demand charges low.',
      '- Double-check whether your plan has an off-peak window; shifting 2–3 hours can shave noticeable costs.',
    ].join('\n');
  }

  if (normalized.includes('device')) {
    const devicesMentioned = history
      .filter((msg) => msg.sender === 'user')
      .map((msg) => msg.text)
      .join(' ')
      .match(/ac|fridge|computer|lights|heater/gi);

    const deviceList = devicesMentioned ? Array.from(new Set(devicesMentioned)).join(', ') : 'your core devices';

    return [
      `Here is a quick checklist for ${deviceList}:`,
      '* Track their standby draw—anything above 30 W idle is worth investigating.',
      '* Note when they spike; pairing that with the dashboard timeline makes anomalies much easier to spot.',
      '* If something sits in “Idle” for hours, consider automating a shutoff rule.',
    ].join('\n');
  }

  if (normalized.includes('forecast') || normalized.includes('predict')) {
    return [
      'Our forecast traces mirror the last 24 h pattern, so you will see a morning ramp, a noon lull, and an evening bump.',
      'When the blue dashed line drifts above the green fill, it means you are tracking hotter than usual—time to trim loads.',
    ].join('\n');
  }

  const randomTip = ENERGY_TIPS[Math.floor(Math.random() * ENERGY_TIPS.length)];
  return `I love that question. ${randomTip}`;
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
        await sleep(650);
        setMessages((prev) => {
          const responseText = craftResponse(input, prev);
          const botMessage: ChatMessage = {
            id: (Date.now() + 1).toString(),
            sender: 'bot',
            text: responseText,
          };
          return [...prev, botMessage];
        });
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading]
  );

  return useMemo(
    () => ({
      messages,
      isLoading,
      sendMessage,
    }),
    [messages, isLoading, sendMessage]
  );
};

export default useChatAssistant;

