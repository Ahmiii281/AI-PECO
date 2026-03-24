import React, { useEffect, useMemo, useState } from 'react';
import { ClockIcon, CurrencyDollarIcon, LightningBoltIcon, TargetIcon } from './Icons';
import StatsCard from './StatsCard';
import EnergyChart from './EnergyChart';
import RecommendationCard from './RecommendationCard';
import SmartAnalysis from './SmartAnalysis';
import useMockData from '../hooks/useMockData';
import DeviceStatusList from './DeviceStatusList';
import NotificationToast from './NotificationToast';
import useDeviceNotifications from '../hooks/useDeviceNotifications';
import FutureForecastChart from './FutureForecastChart';
import { dashboardAPI } from '../services/api';
import authService from '../services/auth';
import { USE_DEMO_DATA } from '../demoConfig';
import type { DashboardStatsSummary } from '../types';

const DashboardView: React.FC = () => {
  const isDemoMode = USE_DEMO_DATA;
  const { liveData, forecastData, recommendations, devices, futureForecastData } = useMockData();
  const { notifications, removeNotification } = useDeviceNotifications(devices);

  const [backendStats, setBackendStats] = useState<DashboardStatsSummary | null>(null);
  const [statsError, setStatsError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const fetchStats = async () => {
      if (!authService.isAuthenticated()) return;
      try {
        const stats = await dashboardAPI.getStats();
        if (isMounted) {
          setBackendStats(stats);
          setStatsError(null);
        }
      } catch (error) {
        console.error('Failed to load dashboard stats from backend', error);
        if (isMounted) {
          setBackendStats(null);
          setStatsError('Using demo data (backend unavailable).');
        }
      }
    };

    fetchStats();

    return () => {
      isMounted = false;
    };
  }, []);

  const currentPowerFromMock = liveData.length > 0 ? liveData[liveData.length - 1].power : 0;
  const totalDailyUsageFromMock = liveData.reduce((total, point) => total + point.power, 0) / 4;
  const dailyCostFromMock = totalDailyUsageFromMock * 30;

  const currentPower =
    backendStats && backendStats.total_power > 0
      ? backendStats.total_power / 1000
      : currentPowerFromMock;

  const totalDailyUsage = totalDailyUsageFromMock;
  const dailyCost = dailyCostFromMock;

  const summaryCards = useMemo(
    () => [
      {
        title: 'Current Power',
        value: `${currentPower.toFixed(2)} kW`,
        icon: <LightningBoltIcon />,
        trend: '3%',
      },
      {
        title: "Today's Usage",
        value: `${totalDailyUsage.toFixed(1)} kWh`,
        icon: <ClockIcon />,
        trend: '5%',
      },
      {
        title: 'Daily Cost',
        value: `PKR ${dailyCost.toFixed(0)}`,
        icon: <CurrencyDollarIcon />,
        trend: '-2%',
      },
    ],
    [totalDailyUsage, dailyCost, currentPower]
  );

  const forecastAccuracy = useMemo(() => {
    if (liveData.length === 0 || forecastData.length === 0 || liveData.length !== forecastData.length) {
      return 0;
    }

    let errorSum = 0;
    let count = 0;

    liveData.forEach((dataPoint, idx) => {
      const realValue = dataPoint.power;
      const predictedValue = forecastData[idx]?.forecast;

      if (predictedValue !== undefined && realValue > 0.1) {
        const difference = Math.abs(realValue - predictedValue) / realValue;
        errorSum += difference;
        count++;
      }
    });

    if (count === 0) {
      return 100;
    }

    const averageError = errorSum / count;
    const accuracyPercent = Math.max(0, 100 * (1 - averageError));

    return accuracyPercent;
  }, [liveData, forecastData]);

  return (
    <>
      {/* Notification Area */}
      <div
        aria-live="assertive"
        className="fixed inset-0 flex items-end px-4 py-6 pointer-events-none sm:p-6 sm:items-start z-50"
      >
        <div className="w-full flex flex-col items-center space-y-4 sm:items-end">
          {notifications.map((notification) => (
            <NotificationToast key={notification.id} notification={notification} onClose={() => removeNotification(notification.id)} />
          ))}
        </div>
      </div>
      <div className="p-4 md:p-6 lg:p-8 space-y-8">
        {/* Top Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {summaryCards.map((card) => (
            <StatsCard key={card.title} {...card} />
          ))}
          <StatsCard title="Forecast Accuracy" value={`${forecastAccuracy.toFixed(1)}%`} icon={<TargetIcon />} />
        </div>

        {backendStats && (
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs sm:text-sm text-gray-500 dark:text-gray-400">
            <p>
              Backend live stats: {backendStats.device_count} device(s), avg temp {backendStats.avg_temperature.toFixed(1)}°C, avg humidity{' '}
              {backendStats.avg_humidity.toFixed(1)}%.
            </p>
            <p>
              Active alerts: <span className="font-semibold">{backendStats.alert_count}</span>
            </p>
          </div>
        )}
        {statsError && !backendStats && (
          <p className="text-xs sm:text-sm text-yellow-600 dark:text-yellow-400">
            {statsError}
          </p>
        )}

        {/* Demo mode banner */}
        {isDemoMode && (
          <div className="rounded-lg border border-dashed border-yellow-400 bg-yellow-50 text-xs sm:text-sm text-yellow-800 px-3 py-2 mb-4">
            You are currently viewing <span className="font-semibold">sample demo data</span> generated in the browser. Backend stats are used when available.
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Chart and Smart Analysis */}
          <div className="lg:col-span-2 space-y-8">
            <EnergyChart liveData={liveData} forecastData={forecastData} />
            <FutureForecastChart data={futureForecastData} />
            <SmartAnalysis consumptionHistory={liveData} />
          </div>

          {/* Right Column: Devices and Recommendations */}
          <div className="space-y-8">
            <DeviceStatusList devices={devices} />
            <div className="bg-white dark:bg-gray-700/50 p-6 rounded-xl shadow-lg border border-gray-200 dark:border-transparent">
              <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Energy Saving Tips</h3>
              <div className="space-y-4">
                {recommendations.map((rec) => (
                  <RecommendationCard key={rec.id} recommendation={rec} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default DashboardView;