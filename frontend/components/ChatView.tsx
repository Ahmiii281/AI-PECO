import React, { useEffect, useRef, useState } from 'react';
import { SparklesIcon } from './Icons';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { ChatMessage } from '../types';
import useChatbot from '../hooks/useChatbot';

const ChatView: React.FC = () => {
    const [input, setInput] = useState('');
    const { messages, isLoading, sendMessage } = useChatbot();
    const messagesEndRef = useRef<null | HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading]);

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const nextInput = input;
        setInput('');
        await sendMessage(nextInput);
    };

        return (
                <div className="flex flex-col h-full bg-[var(--color-bg-primary)]">
            <div className="p-4 border-b border-[var(--color-border-default)] bg-[var(--color-bg-secondary)] sticky top-0 z-10">
                <h2 className="text-xl font-semibold text-[var(--color-text-primary)]">Energy Assistant</h2>
                <p className="text-sm text-[var(--color-text-secondary)]">Ask questions about your energy usage</p>
            </div>
            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
                {messages.map((msg) => (
                    <div key={msg.id} className={`flex items-start gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                        {msg.sender === 'bot' && (
                            <div className="w-8 h-8 rounded-full bg-[var(--color-accent-primary)] flex items-center justify-center flex-shrink-0 text-[var(--color-bg-primary)]">
                                <SparklesIcon/>
                            </div>
                        )}
                        <div className={`max-w-lg lg:max-w-2xl px-4 py-3 rounded-2xl shadow-sm ${msg.sender === 'user' ? 'bg-[var(--color-accent-primary)] text-[var(--color-bg-primary)] rounded-br-none' : 'bg-[var(--color-bg-card)] text-[var(--color-text-primary)] rounded-bl-none'}`}>
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
                            <div className="w-8 h-8 rounded-full bg-[var(--color-accent-primary)] flex items-center justify-center flex-shrink-0 text-[var(--color-bg-primary)]">
                            <SparklesIcon/>
                        </div>
                        <div className="max-w-lg lg:max-w-2xl px-4 py-3 rounded-2xl shadow-sm bg-[var(--color-bg-card)] text-[var(--color-text-primary)] rounded-bl-none">
                            <div className="flex items-center space-x-1.5">
                                <span className="h-2 w-2 rounded-full animate-bounce" style={{ backgroundColor: 'var(--color-text-secondary)', animationDelay: '-0.3s' }}></span>
                                <span className="h-2 w-2 rounded-full animate-bounce" style={{ backgroundColor: 'var(--color-text-secondary)', animationDelay: '-0.15s' }}></span>
                                <span className="h-2 w-2 rounded-full animate-bounce" style={{ backgroundColor: 'var(--color-text-secondary)' }}></span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>
            <div className="p-4 border-t border-[var(--color-border-default)] bg-[var(--color-bg-secondary)]/90 backdrop-blur-sm sticky bottom-0">
                <form onSubmit={handleSendMessage} className="flex items-center gap-3">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type your question here..."
                        className="flex-grow bg-[var(--color-bg-input)] border border-[var(--color-border-default)] rounded-full px-5 py-3 text-[var(--color-text-primary)] focus:ring-2 focus:ring-[var(--color-accent-primary)] focus:outline-none transition-shadow"
                        disabled={isLoading}
                        aria-label="Chat input"
                    />
                    <button
                        type="submit"
                        disabled={isLoading || !input.trim()}
                        className="bg-[var(--color-accent-primary)] hover:bg-[var(--color-accent-primary-dim)] text-[var(--color-bg-primary)] p-3 rounded-full transition-colors disabled:bg-[var(--color-border-default)] dark:disabled:bg-[var(--color-border-default)] disabled:cursor-not-allowed flex items-center justify-center flex-shrink-0"
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
