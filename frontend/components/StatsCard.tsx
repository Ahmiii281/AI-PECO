
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
    <div className="pcb-card p-6 flex items-start justify-between">
      <div>
        <p className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">{title}</p>
        <p className="text-3xl font-bold mt-1 digital-value">{value}</p>
        {trend && (
          <div className={`mt-2 flex items-center text-[10px] font-mono ${isUp ? 'text-emerald-500' : 'text-white'}`}>
            <span className="mr-1">
              {isUp ? '>>' : '<<'}
            </span>
            <span>{trend} STATUS</span>
          </div>
        )}
      </div>
      <div className="bg-emerald-500/5 text-emerald-500 rounded p-2 border border-emerald-500/20">
        {icon}
      </div>
    </div>
  );
};

export default StatsCard;