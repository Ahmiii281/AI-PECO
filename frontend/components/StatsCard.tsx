
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
        <p className="text-[10px] font-mono uppercase tracking-widest text-[var(--color-text-secondary)]">{title}</p>
        <p className="text-3xl font-bold mt-1 digital-value">{value}</p>
        {trend && (
          <div className={`mt-2 flex items-center text-[10px] font-mono ${isUp ? 'text-[var(--color-success)]' : 'text-[var(--color-text-secondary)]'}`}>
            <span className="mr-1">
              {isUp ? '>>' : '<<'}
            </span>
            <span>{trend} STATUS</span>
          </div>
        )}
      </div>
      <div className="bg-[var(--color-accent-primary-dim)]/10 text-[var(--color-accent-primary)] rounded p-2 border border-[var(--color-accent-primary-dim)]">
        {icon}
      </div>
    </div>
  );
};

export default StatsCard;