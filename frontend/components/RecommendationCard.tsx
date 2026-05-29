
import React from 'react';
import { Recommendation } from '../types';
import { LightBulbIcon } from './Icons';

interface RecommendationCardProps {
  recommendation: Recommendation;
  isAI?: boolean;
}

const RecommendationCard: React.FC<RecommendationCardProps> = ({ recommendation, isAI }) => {
  return (
    <div className={`p-4 rounded-lg flex items-start space-x-4 transition-colors ${isAI ? 'bg-cyan-900/20 border border-cyan-500/20 hover:bg-cyan-900/30' : 'bg-gray-100 dark:bg-gray-600/50 hover:bg-gray-200 dark:hover:bg-gray-600'}`}>
      <div className={`flex-shrink-0 mt-1 ${isAI ? 'text-cyan-400' : 'text-yellow-500 dark:text-yellow-400'}`}>
        <LightBulbIcon />
      </div>
      <div>
        <div className="flex items-center gap-2">
          <h4 className="font-semibold text-gray-800 dark:text-white">{recommendation.title}</h4>
          {isAI && (
            <span className="text-[8px] font-mono uppercase tracking-wider bg-cyan-500/20 text-cyan-400 px-1.5 py-0.5 rounded">RL</span>
          )}
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{recommendation.description}</p>
        <p className="text-xs text-green-600 dark:text-green-400 mt-2 font-mono">Savings: ~{recommendation.estimatedSavings}</p>
      </div>
    </div>
  );
};

export default RecommendationCard;