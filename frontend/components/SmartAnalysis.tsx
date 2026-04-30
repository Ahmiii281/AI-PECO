
import React, { useState } from 'react';
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

  const calculateStats = (dataPoints: DataPoint[]) => {
    const last24Points = dataPoints.slice(-24);
    const sumPower = last24Points.reduce((total, point) => total + point.power, 0);
    const avgPower = last24Points.length > 0 ? sumPower / last24Points.length : 0;

    const highestPoint = last24Points.reduce(
      (max, point) => (point.power > max.power ? point : max),
      { power: 0, time: '' } as Pick<DataPoint, 'power' | 'time'>
    );

    const lowestPoint = last24Points.reduce(
      (min, point) => (min.power === 0 || point.power < min.power ? point : min),
      { power: 0, time: '' } as Pick<DataPoint, 'power' | 'time'>
    );

    return { total: sumPower, average: avgPower, peak: highestPoint, lowest: lowestPoint };
  };

  const buildResponse = (question: string, history: DataPoint[]) => {
    if (!history.length) {
      return 'There is no data available yet. Please wait a few minutes for data to be collected and try again.';
    }

    const { total, average, peak, lowest } = calculateStats(history);
    const dailyKwh = (total / 4).toFixed(2);
    const avgKw = average.toFixed(2);

    const introText = question.toLowerCase().includes('why') ? 'Here is what I found:' : 'Summary:';

    return [
      `### ${introText}`,
      `- **Daily consumption:** Approximately ${dailyKwh} kWh in the last 24 hours.`,
      `- **Average power:** ${avgKw} kW. Values above this indicate high usage.`,
      `- **Highest usage:** ${peak.power.toFixed(2)} kW at ${peak.time}.`,
      `- **Lowest usage:** ${lowest.power.toFixed(2)} kW at ${lowest.time}.`,
      '',
      'Recommendations:',
      '* Move one high-power device to a different time to avoid the peak period.',
      '* Check devices that stay above 0.5 kW even when idle - they may be wasting power.',
      '* Use the Devices page to see which specific device is causing high consumption.',
    ].join('\n');
  };

  const handleAnalysis = async () => {
    if (!query.trim()) {
      setError('Please enter a question.');
      return;
    }
    setIsLoading(true);
    setError('');
    setResponse('');
    await new Promise((resolve) => setTimeout(resolve, 800));
    const result = buildResponse(query, consumptionHistory);
    setResponse(result);
    setIsLoading(false);
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
    <div className="pcb-card p-6">
      <div className="flex items-center mb-4">
        <div className="text-emerald-500 animate-pulse">
          <SparklesIcon />
        </div>
        <h3 className="text-xl font-semibold ml-2 text-white font-mono uppercase tracking-tighter">AI <span className="text-emerald-500">CORE</span></h3>
      </div>
      <p className="text-zinc-500 mb-6 text-[10px] font-mono uppercase tracking-[0.2em]">Diagnostic interface and consumption analysis.</p>
      
      <div className="flex flex-col md:flex-row gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="ENTER_QUERY..."
          className="flex-grow bg-black border border-zinc-800 rounded px-4 py-2 text-emerald-500 placeholder-zinc-800 focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 focus:outline-none transition-all font-mono text-xs"
          disabled={isLoading}
        />
        <button
          onClick={handleAnalysis}
          disabled={isLoading}
          className="bg-emerald-600 hover:bg-emerald-500 text-black font-bold py-2 px-8 rounded transition-all active:scale-95 disabled:opacity-20 disabled:cursor-not-allowed flex items-center justify-center font-mono text-xs uppercase tracking-widest"
        >
          {isLoading ? 'EXECUTING...' : 'RUN_PROC'}
        </button>
      </div>

      {error && <p className="text-white mt-4 font-mono text-[9px] uppercase bg-red-900/20 p-2 border border-red-900/50">ERR_EXCEPTION: {error}</p>}
      
      {response && (
        <div className="mt-8 p-5 bg-black rounded border border-zinc-900 shadow-inner">
           <div className="prose prose-sm max-w-none text-zinc-300 font-sans leading-relaxed">
              {renderResponse(response)}
           </div>
           <div className="mt-4 pt-4 border-t border-zinc-900 text-[9px] font-mono text-zinc-700 uppercase tracking-widest">
             CORE_REPORT_GEN_AUTO
           </div>
        </div>
      )}
    </div>
  );
};

export default SmartAnalysis;