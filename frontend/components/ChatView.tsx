import React, { useEffect, useRef, useState } from 'react';
import { SparklesIcon } from './Icons';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { ChatMessage } from '../types';

const WELCOME_MESSAGE: ChatMessage = {
    id: 'welcome',
    sender: 'bot',
    text: "Hello! I'm your energy assistant powered by Reinforcement Learning. I can help you understand your power consumption, save money on bills, and optimize your device usage. Try asking about costs, forecasts, or how to save energy.",
};

const SYSTEM_PROMPT = `You are an AI energy assistant for AI-PECO, a smart home energy monitoring system. Help users understand their electricity consumption, reduce bills, optimize device usage, and interpret energy forecasts. Be concise, practical, and focused on energy topics. Format responses in markdown when helpful.`;

const ChatView: React.FC = () => {
    const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
    const [isLoading, setIsLoading] = useState(false);
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<null | HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading]);

    const sendMessage = async (userInput: string) => {
        const trimmed = userInput.trim();
        if (!trimmed || isLoading) return;

        const userMsg: ChatMessage = { id: `${Date.now()}`, sender: 'user', text: trimmed };
        setMessages((m) => [...m, userMsg]);
        setIsLoading(true);

        const apiKey = (import.meta as any).env.VITE_OPENAI_API_KEY;
        if (!apiKey) {
            const errMsg: ChatMessage = { id: `err-${Date.now()}`, sender: 'bot', text: '⚠️ OpenAI API key not configured. Add VITE_OPENAI_API_KEY to your .env file.' };
            setMessages((m) => [...m, errMsg]);
            setIsLoading(false);
            return;
        }

        // Prepare conversation history (exclude welcome message)
        const history = messages
            .filter((m) => m.id !== 'welcome')
            .map((m) => ({ role: m.sender === 'user' ? 'user' : 'assistant', content: m.text }));

        const payload = {
            model: 'gpt-4o-mini',
            messages: [
                { role: 'system', content: SYSTEM_PROMPT },
                ...history,
                { role: 'user', content: trimmed },
            ],
            max_tokens: 500,
            temperature: 0.7,
        };

        try {
            const res = await fetch('https://api.openai.com/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${apiKey}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!res.ok) {
                const txt = await res.text();
                throw new Error(`OpenAI API error: ${res.status} ${txt}`);
            }

            const data = await res.json();
            const botText = data?.choices?.[0]?.message?.content ?? 'Sorry, I could not generate a response.';

            const botMsg: ChatMessage = { id: `${Date.now() + 1}`, sender: 'bot', text: botText };
            setMessages((m) => [...m, botMsg]);
        } catch (err: any) {
            const errMsg: ChatMessage = { id: `err-${Date.now()}`, sender: 'bot', text: err?.message || 'An error occurred while getting a response.' };
            setMessages((m) => [...m, errMsg]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const nextInput = input;
        setInput('');
        await sendMessage(nextInput);
    };

        return (
                <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-800">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900/50 sticky top-0 z-10">
                <h2 className="text-xl font-semibold text-gray-800 dark:text-white">Energy Assistant</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">Ask questions about your energy usage</p>
            </div>
            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
                {messages.map((msg) => (
                    <div key={msg.id} className={`flex items-start gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                        {msg.sender === 'bot' && (
                            <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0 text-white">
                                <SparklesIcon/>
                            </div>
                        )}
                        <div className={`max-w-lg lg:max-w-2xl px-4 py-3 rounded-2xl shadow-sm ${msg.sender === 'user' ? 'bg-green-600 text-white rounded-br-none' : 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-bl-none'}`}>
                           <div 
                                    className="prose prose-sm dark:prose-invert max-w-none text-gray-800 dark:text-gray-200"
                                    dangerouslySetInnerHTML={{ 
                                      __html: DOMPurify.sanitize(marked.parse(msg.text) as string) 
                                    }} 
                                  />
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex items-start gap-3 justify-start">
                        <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0 text-white">
                            <SparklesIcon/>
                        </div>
                        <div className="max-w-lg lg:max-w-2xl px-4 py-3 rounded-2xl shadow-sm bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-bl-none">
                            <div className="flex items-center space-x-1.5">
                                <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                                <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                                <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce"></span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>
            <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm sticky bottom-0">
                <form onSubmit={handleSendMessage} className="flex items-center gap-3">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type your question here..."
                        className="flex-grow bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-full px-5 py-3 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500 focus:outline-none transition-shadow"
                        disabled={isLoading}
                        aria-label="Chat input"
                    />
                    <button
                        type="submit"
                        disabled={isLoading || !input.trim()}
                        className="bg-green-600 hover:bg-green-700 text-white p-3 rounded-full transition-colors disabled:bg-gray-400 dark:disabled:bg-gray-500 disabled:cursor-not-allowed flex items-center justify-center flex-shrink-0"
                        aria-label="Send message"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 transform rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ChatView;
