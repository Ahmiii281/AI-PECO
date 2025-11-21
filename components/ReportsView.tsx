
import React, { useState, useMemo } from 'react';
import { ResponsiveContainer, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Bar, PieChart, Pie, Cell, Sector } from 'recharts';
import useMockData from '../hooks/useMockData';
import { DataPoint, Anomaly } from '../types';
import StatsCard from './StatsCard';
import { CalculatorIcon, ClockIcon, CurrencyDollarIcon, LightningBoltIcon, DownloadIcon, ShieldExclamationIcon, ExclamationCircleIcon } from './Icons';
import { useTheme } from '../contexts/ThemeContext';

type TimeRange = '24h' | '7d' | '30d';

// --- Custom Components for Charts ---

const CustomBarTooltip = ({ active, payload, label }: any) => {
  const { theme } = useTheme();
  if (active && payload && payload.length) {
    const containerClass = theme === 'dark' 
      ? 'bg-gray-800/80 border-gray-600' 
      : 'bg-white/80 border-gray-200';

    return (
      <div className={`p-3 rounded-lg shadow-xl border ${containerClass} backdrop-blur-sm animate-fade-in-scale`}>
        <p className="label text-sm font-semibold text-gray-500 dark:text-gray-400 mb-1">{label}</p>
        <div className="intro flex items-center font-bold text-gray-800 dark:text-white">
          <span className="mr-2 h-2.5 w-2.5 rounded-full" style={{ backgroundColor: payload[0].fill }}></span>
          <span>{`${payload[0].name}: ${payload[0].value} kWh`}</span>
        </div>
      </div>
    );
  }
  return null;
};

const CustomPieTooltip = ({ active, payload }: any) => {
    const { theme } = useTheme();
    if (active && payload && payload.length) {
        const data = payload[0];
        const containerClass = theme === 'dark' 
            ? 'bg-gray-800/80 border-gray-600' 
            : 'bg-white/80 border-gray-200';

        return (
            <div className={`p-3 rounded-lg shadow-xl border ${containerClass} backdrop-blur-sm animate-fade-in-scale`}>
                <p className="font-semibold flex items-center" style={{ color: data.payload.fill }}>
                    <span className="mr-2 h-2.5 w-2.5 rounded-full" style={{ backgroundColor: data.payload.fill }}></span>
                    {data.name}: {data.value.toLocaleString()} kWh ({`${(data.percent * 100).toFixed(0)}%`})
                </p>
            </div>
        );
    }
    return null;
};


const renderActiveShape = (props: any) => {
  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill, payload } = props;

  return (
    <g>
      <text x={cx} y={cy - 18} textAnchor="middle" className="text-base font-bold dark:fill-white fill-gray-800">
        {payload.name}
      </text>
      <text x={cx} y={cy + 5} textAnchor="middle" className="text-2xl font-mono font-bold dark:fill-white fill-gray-800">
        {`${payload.value.toLocaleString()}`}
        <tspan className="text-lg" dy="-0.2em">kWh</tspan>
      </text>
       <text x={cx} y={cy + 28} textAnchor="middle" className="text-sm dark:fill-gray-400 fill-gray-500">
        {`(${(payload.percent * 100).toFixed(0)}% of total)`}
      </text>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
      />
    </g>
  );
};


// --- Main View Component ---

const ReportsView: React.FC = () => {
  const [timeRange, setTimeRange] = useState<TimeRange>('7d');
  const [showAnomalousOnly, setShowAnomalousOnly] = useState(false);
  const { historicalData, perDeviceHistoricalData, anomalies } = useMockData();
  const { theme } = useTheme();
  const [activeIndex, setActiveIndex] = useState(0);

  const onPieEnter = (_: any, index: number) => {
      setActiveIndex(index);
  };
  
  const tickColor = theme === 'dark' ? '#9ca3af' : '#6b7280';
  const gridColor = theme === 'dark' ? '#444444' : '#e5e7eb';
  
  const getCutoffDate = (range: TimeRange): Date => {
      const now = new Date();
      let daysToFilter;
      switch (range) {
        case '24h': daysToFilter = 1; break;
        case '7d': daysToFilter = 7; break;
        case '30d': daysToFilter = 30; break;
        default: daysToFilter = 7;
      }
      return new Date(now.getTime() - daysToFilter * 24 * 60 * 60 * 1000);
  };

  const anomaliesInTimeRange = useMemo(() => {
    const cutoffDate = getCutoffDate(timeRange);
    return anomalies.filter(a => a.timestamp > cutoffDate);
  }, [timeRange, anomalies]);

  const anomalousDeviceIdsInTimeRange = useMemo(() => {
    return new Set(anomaliesInTimeRange.map(a => a.deviceId));
  }, [anomaliesInTimeRange]);
  
  const filteredData = useMemo(() => {
    const cutoffDate = getCutoffDate(timeRange);
    
    if (!showAnomalousOnly) {
      return historicalData.filter(d => d.date > cutoffDate);
    }
    
    // Aggregate data only from devices that have anomalies in the selected time range
    const dataToAggregate = Object.entries(perDeviceHistoricalData)
      .filter(([deviceId]) => anomalousDeviceIdsInTimeRange.has(deviceId))
      .map(([, data]) => data)
      .flat()
      .filter(d => d.date > cutoffDate);

    const aggregatedMap = new Map<number, { totalPower: number, count: number }>();
    dataToAggregate.forEach(dp => {
        const timeKey = dp.date.getTime();
        const existing = aggregatedMap.get(timeKey) || { totalPower: 0, count: 0 };
        existing.totalPower += dp.power;
        existing.count = 1; // It's a sum of a subset of devices now
        aggregatedMap.set(timeKey, existing);
    });
    
    return Array.from(aggregatedMap.entries()).map(([ts, { totalPower }]) => ({
      date: new Date(ts),
      time: new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      power: totalPower
    }));

  }, [timeRange, historicalData, perDeviceHistoricalData, showAnomalousOnly, anomalousDeviceIdsInTimeRange]);

  const aggregatedData = useMemo(() => {
     if (timeRange === '24h') {
        const hourlyMap = new Map<string, number>();
        filteredData.forEach(dp => {
            const hourKey = `${dp.date.getFullYear()}-${dp.date.getMonth()}-${dp.date.getDate()}T${dp.date.getHours()}`;
            hourlyMap.set(hourKey, (hourlyMap.get(hourKey) || 0) + dp.power);
        });
        return Array.from(hourlyMap.entries()).map(([time, power]) => ({
            name: new Date(time).toLocaleTimeString([], { weekday: 'short', hour: 'numeric' }),
            consumption: parseFloat(power.toFixed(1))
        }));
    } else {
        const dailyMap = new Map<string, number>();
        filteredData.forEach(dp => {
            const day = dp.date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            dailyMap.set(day, (dailyMap.get(day) || 0) + dp.power);
        });
        return Array.from(dailyMap.entries()).map(([day, power]) => ({
            name: day,
            consumption: parseFloat((power/24).toFixed(1))
        }));
    }
  }, [filteredData, timeRange]);
  
  const summaryStats = useMemo(() => {
    if (filteredData.length === 0) return { total: 0, avg: 0, cost: 0, peak: 0 };
    const total = filteredData.reduce((sum, d) => sum + d.power, 0) / 24;
    const avg = total / (filteredData.length > 0 ? (new Set(filteredData.map(d => d.date.toDateString())).size) : 1);
    const cost = total * 30; // Example rate: PKR 30 per kWh
    const peak = Math.max(...filteredData.map(d => d.power));
    return { total, avg, cost, peak };
  }, [filteredData, timeRange]);
  
  const peakVsOffPeakData = useMemo(() => {
    let peak = 0;
    let offPeak = 0;
    filteredData.forEach(dp => {
        const hour = dp.date.getHours();
        if (hour >= 7 && hour < 21) { peak += dp.power; } 
        else { offPeak += dp.power; }
    });
    return [ {name: 'Peak Hours', value: parseFloat(peak.toFixed(1))}, {name: 'Off-Peak Hours', value: parseFloat(offPeak.toFixed(1))} ];
  }, [filteredData]);
  
  const COLORS = ['#ef4444', '#22c55e'];

  const handleExport = () => {
    if (!aggregatedData.length) return;
    let csvContent = ["Date/Time,Consumption (kWh)", ...aggregatedData.map(item => `${item.name},${item.consumption}`)].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.download = `energy_report_${timeRange}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const TimeRangeButton: React.FC<{ range: TimeRange; label: string }> = ({ range, label }) => (
    <button onClick={() => setTimeRange(range)} className={`px-4 py-2 text-sm font-semibold rounded-md transition-colors ${timeRange === range ? 'bg-green-600 text-white' : 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-500'}`}>
      {label}
    </button>
  );

  return (
    <div className="p-4 md:p-6 lg:p-8 space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 dark:text-white">Reports & Analytics</h1>
          <p className="text-md text-gray-500 dark:text-gray-400">Analyze historical data and gain insights into your energy usage.</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
            <TimeRangeButton range="24h" label="24h" />
            <TimeRangeButton range="7d" label="7d" />
            <TimeRangeButton range="30d" label="30d" />
            <button onClick={handleExport} className="p-2.5 rounded-md bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors" title="Export Data as CSV">
              <DownloadIcon />
            </button>
        </div>
      </div>
      
      <div className="flex items-center space-x-3 bg-gray-100 dark:bg-gray-700/50 p-3 rounded-lg">
        <label htmlFor="anomaly-toggle" className="text-sm font-medium text-gray-600 dark:text-gray-300 cursor-pointer">
          Show Anomalous Devices Only
        </label>
        <div className="relative inline-flex items-center cursor-pointer">
          <input type="checkbox" id="anomaly-toggle" className="sr-only peer" checked={showAnomalousOnly} onChange={(e) => setShowAnomalousOnly(e.target.checked)} />
          <div className="w-11 h-6 bg-gray-300 dark:bg-gray-600 rounded-full peer peer-focus:ring-2 peer-focus:ring-yellow-400 dark:peer-focus:ring-yellow-800 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-yellow-500"></div>
        </div>
        {showAnomalousOnly && <p className="text-xs text-gray-500 dark:text-gray-400">Showing aggregated data for {anomalousDeviceIdsInTimeRange.size} device(s) with anomalies.</p>}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard title="Total Consumption" value={`${summaryStats.total.toFixed(1)} kWh`} icon={<CalculatorIcon />} />
        <StatsCard title="Avg. Daily Usage" value={`${summaryStats.avg.toFixed(1)} kWh`} icon={<ClockIcon />} />
        <StatsCard title="Estimated Cost" value={`PKR ${summaryStats.cost.toFixed(0)}`} icon={<CurrencyDollarIcon />} />
        <StatsCard title="Peak Usage" value={`${summaryStats.peak.toFixed(2)} kW`} icon={<LightningBoltIcon />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-white dark:bg-gray-700/50 p-4 sm:p-6 rounded-xl shadow-lg h-96 border border-gray-200 dark:border-transparent">
            <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Historical Consumption</h3>
            <ResponsiveContainer width="100%" height="85%">
                <BarChart data={aggregatedData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={gridColor}/>
                    <XAxis dataKey="name" stroke={tickColor} tick={{ fontSize: 12 }}/>
                    <YAxis stroke={tickColor} tick={{ fontSize: 12 }} label={{ value: 'kWh', angle: -90, position: 'insideLeft', fill: tickColor, fontSize: 14 }}/>
                    <Tooltip content={<CustomBarTooltip />} cursor={{fill: theme === 'dark' ? 'rgba(110, 231, 183, 0.1)' : 'rgba(16, 185, 129, 0.1)'}}/>
                    <Legend wrapperStyle={{color: tickColor}} />
                    <Bar dataKey="consumption" fill="#34d399" name="Consumption (kWh)" barSize={20} radius={[4, 4, 0, 0]} animationDuration={800} />
                </BarChart>
            </ResponsiveContainer>
        </div>
        <div className="bg-white dark:bg-gray-700/50 p-4 sm:p-6 rounded-xl shadow-lg h-96 border border-gray-200 dark:border-transparent">
            <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Peak vs. Off-Peak</h3>
            <ResponsiveContainer width="100%" height="85%">
                <PieChart>
                    <Pie
                      activeIndex={activeIndex}
                      activeShape={renderActiveShape}
                      data={peakVsOffPeakData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      onMouseEnter={onPieEnter}
                      animationDuration={500}
                      animationEasing="ease-out"
                    >
                        {peakVsOffPeakData.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke={theme === 'dark' ? '#2d2d2d' : '#ffffff'} strokeWidth={3} />)}
                    </Pie>
                    <Tooltip content={<CustomPieTooltip />} />
                    <Legend wrapperStyle={{color: tickColor, paddingTop: '20px'}} iconSize={12} />
                </PieChart>
            </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-700/50 p-4 sm:p-6 rounded-xl shadow-lg border border-gray-200 dark:border-transparent">
        <div className="flex items-center mb-4">
          <ShieldExclamationIcon />
          <h3 className="text-xl font-semibold ml-3 text-gray-900 dark:text-white">Anomaly Log</h3>
        </div>
        <div className="overflow-x-auto max-h-96">
          {anomaliesInTimeRange.length > 0 ? (
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-600">
              <thead className="bg-gray-50 dark:bg-gray-800 sticky top-0">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Device</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Type</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Details</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Timestamp</th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-700/40 divide-y divide-gray-200 dark:divide-gray-600">
                {anomaliesInTimeRange.map((anomaly) => (
                  <tr key={anomaly.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">{anomaly.deviceName}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${anomaly.type === 'high' ? 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300' : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300'}`}>
                        {anomaly.type === 'high' ? 'High Usage' : 'Low Usage'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                      <div className="flex items-center">
                        <span className={`mr-2 ${anomaly.type === 'high' ? 'text-red-500' : 'text-yellow-500'}`}><ExclamationCircleIcon/></span>
                        <div>
                          <span className="font-bold">{anomaly.value}W</span>
                          <span className="text-xs"> (Normal: {anomaly.normalRange.join('-')}W)</span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                        <div>{anomaly.timestamp.toLocaleString()}</div>
                        <div className="text-xs text-gray-500">Duration: ~{anomaly.duration} mins</div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-center text-gray-500 dark:text-gray-400 py-12">No anomalies detected in the selected period.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportsView;
