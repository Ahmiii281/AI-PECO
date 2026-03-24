
import React from 'react';

interface StatsCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  trend?: string;
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon, trend }) => {
  const isUp = trend && parseFloat(trend) > 0;
  const isDown = trend && parseFloat(trend) < 0;

  return (
    <div className="bg-white dark:bg-gray-700/50 p-6 rounded-xl shadow-lg flex items-start justify-between transform hover:scale-105 transition-transform duration-300 border border-gray-200 dark:border-transparent">
      <div>
        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
        <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">{value}</p>
        {trend && (
          <div className={`mt-2 flex items-center text-sm ${isUp ? 'text-green-500 dark:text-green-400' : 'text-red-500 dark:text-red-400'}`}>
            <span className="w-5 h-5">
              {isUp ? '▲' : '▼'}
            </span>
            <span>{trend} vs yesterday</span>
          </div>
        )}
      </div>
      <div className="bg-green-100 dark:bg-green-500/20 text-green-500 dark:text-green-400 rounded-full p-3">
        {icon}
      </div>
    </div>
  );
};

export default StatsCard;