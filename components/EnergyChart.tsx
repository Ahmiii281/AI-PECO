
import React from 'react';
import { ResponsiveContainer, AreaChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Line, Area } from 'recharts';
import { DataPoint } from '../types';
import { useTheme } from '../contexts/ThemeContext';

interface EnergyChartProps {
  liveData: DataPoint[];
  forecastData: DataPoint[];
}

const EnergyChart: React.FC<EnergyChartProps> = ({ liveData, forecastData }) => {
  const { theme } = useTheme();

  const combinedData = liveData.map((ld, index) => ({
    ...ld,
    forecast: forecastData[index]?.forecast
  }));
  
  const tickColor = theme === 'dark' ? '#9ca3af' : '#6b7280';
  const gridColor = theme === 'dark' ? '#444444' : '#e5e7eb';
  const tooltipStyle = theme === 'dark' 
    ? { backgroundColor: '#1e1e1e', border: '1px solid #444' }
    : { backgroundColor: '#ffffff', border: '1px solid #ccc' };
  const labelStyle = theme === 'dark' ? { color: '#e5e7eb' } : { color: '#374151' };


  return (
    <div className="bg-white dark:bg-gray-700/50 p-4 sm:p-6 rounded-xl shadow-lg h-96 border border-gray-200 dark:border-transparent">
      <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Energy Consumption (Last 24h)</h3>
      <ResponsiveContainer width="100%" height="85%">
        <AreaChart data={combinedData} margin={{ top: 5, right: 20, left: -10, bottom: 40 }}>
          <defs>
            <linearGradient id="colorPower" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#34d399" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#34d399" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
          <XAxis 
            dataKey="time" 
            stroke={tickColor} 
            tick={{ fontSize: 12 }} 
            angle={-45} 
            textAnchor="end"
            height={60}
            interval={Math.floor(combinedData.length / 8)}
          />
          <YAxis stroke={tickColor} tick={{ fontSize: 12 }} label={{ value: 'Power (kW)', angle: -90, position: 'insideLeft', fill: tickColor, fontSize: 14 }} />
          <Tooltip 
            contentStyle={tooltipStyle}
            labelStyle={labelStyle}
          />
          <Legend wrapperStyle={labelStyle} />
          <Area type="monotone" dataKey="power" name="Live Usage" stroke="#34d399" fillOpacity={1} fill="url(#colorPower)" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="forecast" name="Forecast" stroke="#60a5fa" strokeWidth={2} strokeDasharray="5 5" dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default EnergyChart;