
import React, { useState } from 'react';
import { runSmartAnalysis } from '../services/geminiService';
import { DataPoint } from '../types';
import { SparklesIcon } from './Icons';

interface SmartAnalysisProps {
  consumptionHistory: DataPoint[];
}

const SmartAnalysis: React.FC<SmartAnalysisProps> = ({ consumptionHistory }) => {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAnalysis = async () => {
    if (!query.trim()) {
      setError('Please enter a query.');
      return;
    }
    setIsLoading(true);
    setError('');
    setResponse('');
    try {
      const result = await runSmartAnalysis(query, consumptionHistory);
      setResponse(result);
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderResponse = (text: string) => {
    // Basic markdown-like rendering
    return text.split('\n').map((line, index) => {
      if (line.startsWith('### ')) return <h3 key={index} className="text-lg font-semibold mt-4 mb-2">{line.substring(4)}</h3>
      if (line.startsWith('## ')) return <h2 key={index} className="text-xl font-bold mt-4 mb-2">{line.substring(3)}</h2>
      if (line.startsWith('# ')) return <h1 key={index} className="text-2xl font-bold mt-4 mb-2">{line.substring(2)}</h1>
      if (line.startsWith('* ')) return <li key={index} className="ml-6 list-disc">{line.substring(2)}</li>
      if (line.trim() === '') return <br key={index} />
      return <p key={index} className="my-1">{line}</p>
    })
  }

  return (
    <div className="bg-white dark:bg-gray-700/50 p-6 rounded-xl shadow-lg border border-gray-200 dark:border-transparent">
      <div className="flex items-center mb-4">
        <SparklesIcon />
        <h3 className="text-xl font-semibold ml-2 text-gray-900 dark:text-white">Smart Analysis (Thinking Mode)</h3>
      </div>
      <p className="text-gray-500 dark:text-gray-400 mb-4 text-sm">Ask complex questions about your energy usage. Our AI will provide a detailed analysis.</p>
      
      <div className="flex flex-col md:flex-row gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., 'Why was my consumption high yesterday afternoon?'"
          className="flex-grow bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-4 py-2 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500 focus:outline-none"
          disabled={isLoading}
        />
        <button
          onClick={handleAnalysis}
          disabled={isLoading}
          className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded-md transition-colors disabled:bg-gray-400 dark:disabled:bg-gray-500 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Thinking...
            </>
          ) : 'Analyze'}
        </button>
      </div>

      {error && <p className="text-red-500 dark:text-red-400 mt-4">{error}</p>}
      
      {response && (
        <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
           <div className="prose prose-sm max-w-none text-gray-700 dark:text-gray-300">
              {renderResponse(response)}
           </div>
        </div>
      )}
    </div>
  );
};

export default SmartAnalysis;