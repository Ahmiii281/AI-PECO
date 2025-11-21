import React, { useMemo } from 'react';
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

const DashboardView: React.FC = () => {
  const { liveData, forecastData, recommendations, devices, futureForecastData } = useMockData();
  const { notifications, removeNotification } = useDeviceNotifications(devices);

  const latestPower = liveData.length > 0 ? liveData[liveData.length - 1].power : 0;
  const dailyConsumption = liveData.reduce((sum, d) => sum + d.power, 0) / 4; // Assuming 15min intervals
  const estimatedCost = dailyConsumption * 30; // Example rate: PKR 30 per kWh

  const summaryCards = useMemo(
    () => [
      {
        title: 'Live Power',
        value: `${latestPower.toFixed(2)} kW`,
        icon: <LightningBoltIcon />,
        trend: '3%',
      },
      {
        title: "Today's Consumption",
        value: `${dailyConsumption.toFixed(1)} kWh`,
        icon: <ClockIcon />,
        trend: '5%',
      },
      {
        title: 'Estimated Cost',
        value: `PKR ${estimatedCost.toFixed(0)}`,
        icon: <CurrencyDollarIcon />,
        trend: '-2%',
      },
    ],
    [dailyConsumption, estimatedCost, latestPower]
  );

  // Calculate forecast accuracy based on live and forecast data
  const forecastAccuracy = useMemo(() => {
    if (liveData.length === 0 || forecastData.length === 0 || liveData.length !== forecastData.length) {
      return 0;
    }

    let totalPercentageError = 0;
    let validPoints = 0;

    liveData.forEach((ld, index) => {
      const actual = ld.power;
      const forecast = forecastData[index]?.forecast;

      // Use a small threshold to avoid division by zero or near-zero, which can skew results
      if (forecast !== undefined && actual > 0.1) {
        const error = Math.abs(actual - forecast) / actual;
        totalPercentageError += error;
        validPoints++;
      }
    });

    if (validPoints === 0) {
      return 100; // If no valid points (e.g., all consumption is zero), accuracy is perfect
    }

    const meanAbsolutePercentageError = totalPercentageError / validPoints;
    const accuracy = Math.max(0, 100 * (1 - meanAbsolutePercentageError));

    return accuracy;
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
              <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">AI Recommendations</h3>
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