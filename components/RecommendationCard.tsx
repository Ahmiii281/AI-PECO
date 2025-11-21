
import React from 'react';
import { Recommendation } from '../types';
import { LightBulbIcon } from './Icons';

interface RecommendationCardProps {
  recommendation: Recommendation;
}

const RecommendationCard: React.FC<RecommendationCardProps> = ({ recommendation }) => {
  return (
    <div className="bg-gray-100 dark:bg-gray-600/50 p-4 rounded-lg flex items-start space-x-4 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
      <div className="flex-shrink-0 text-yellow-500 dark:text-yellow-400 mt-1">
        <LightBulbIcon />
      </div>
      <div>
        <h4 className="font-semibold text-gray-800 dark:text-white">{recommendation.title}</h4>
        <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{recommendation.description}</p>
        <p className="text-xs text-green-600 dark:text-green-400 mt-2 font-mono">Savings: ~{recommendation.estimatedSavings}</p>
      </div>
    </div>
  );
};

export default RecommendationCard;