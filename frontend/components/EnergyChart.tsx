
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
  
  const axisColor = '#666666';
  const gridLineColor = '#1A1A1A';
  const tooltipBg = { backgroundColor: '#000000', border: '1px solid #00FF41', borderRadius: '4px', color: '#FFFFFF' };
  const textColor = { color: '#FFFFFF' };


  return (
    <div className="pcb-card p-4 sm:p-6 h-96">
      <h3 className="text-xl font-semibold mb-4 text-white font-mono tracking-tighter uppercase">Power <span className="text-emerald-500">Monitor</span></h3>
      <ResponsiveContainer width="100%" height="85%">
        <AreaChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 40 }}>
          <defs>
            <linearGradient id="powerGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00FF41" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#00FF41" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={gridLineColor} vertical={false} />
          <XAxis 
            dataKey="time" 
            stroke={axisColor} 
            tick={{ fontSize: 10, fill: axisColor, fontFamily: 'monospace' }} 
            angle={-45} 
            textAnchor="end"
            height={60}
            interval={Math.floor(chartData.length / 8)}
          />
          <YAxis stroke={axisColor} tick={{ fontSize: 10, fill: axisColor, fontFamily: 'monospace' }} label={{ value: 'kW', angle: -90, position: 'insideLeft', fill: axisColor, fontSize: 10, fontFamily: 'monospace' }} />
          <Tooltip 
            contentStyle={tooltipBg}
            itemStyle={{ color: '#00FF41', fontFamily: 'monospace' }}
            labelStyle={{ color: '#FFFFFF', marginBottom: '4px', borderBottom: '1px solid #333333' }}
          />
          <Legend wrapperStyle={{ ...textColor, fontFamily: 'monospace', fontSize: '10px', paddingTop: '20px' }} />
          <Area type="monotone" dataKey="power" name="REAL_TIME" stroke="#00FF41" fillOpacity={1} fill="url(#powerGradient)" strokeWidth={2} dot={false} />
          <Area type="monotone" dataKey="forecast" name="FORECAST" stroke="#FFFFFF" fillOpacity={0} strokeWidth={1} strokeDasharray="5 5" dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default EnergyChart;