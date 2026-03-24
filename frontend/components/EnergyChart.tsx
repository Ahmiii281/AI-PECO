
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

  const chartData = liveData.map((dataPoint, idx) => ({
    ...dataPoint,
    forecast: forecastData[idx]?.forecast
  }));
  
  const axisColor = '#2F180B';
  const gridLineColor = '#C0B39E';
  const tooltipBg = { backgroundColor: '#FFFFFF', border: '1px solid #D0C1A9' };
  const textColor = { color: '#2F180B' };


  return (
    <div className="bg-white dark:bg-gray-700/50 p-4 sm:p-6 rounded-xl shadow-lg h-96 border border-gray-200 dark:border-transparent">
      <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Energy Consumption (Last 24h)</h3>
      <ResponsiveContainer width="100%" height="85%">
        <AreaChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 40 }}>
          <defs>
            <linearGradient id="powerGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#5C341E" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#5C341E" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={gridLineColor} />
          <XAxis 
            dataKey="time" 
            stroke={axisColor} 
            tick={{ fontSize: 12 }} 
            angle={-45} 
            textAnchor="end"
            height={60}
            interval={Math.floor(chartData.length / 8)}
          />
          <YAxis stroke={axisColor} tick={{ fontSize: 12 }} label={{ value: 'Power (kW)', angle: -90, position: 'insideLeft', fill: axisColor, fontSize: 14 }} />
          <Tooltip 
            contentStyle={tooltipBg}
            labelStyle={textColor}
          />
          <Legend wrapperStyle={textColor} />
          <Area type="monotone" dataKey="power" name="Live Usage" stroke="#5C341E" fillOpacity={1} fill="url(#powerGradient)" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="forecast" name="Forecast" stroke="#D0C1A9" strokeWidth={2} strokeDasharray="5 5" dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default EnergyChart;