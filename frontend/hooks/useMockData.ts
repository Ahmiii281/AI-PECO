
import { useState, useEffect, useMemo } from 'react';
import { DataPoint, Recommendation, Device, DeviceStatus, PerDeviceHistoricalData, Anomaly } from '../types';

const mockRecommendations: Recommendation[] = [
  { id: '1', title: 'Shift AC Usage', description: 'Run your AC during off-peak hours (after 10 PM) to save on tariff costs.', estimatedSavings: 'PKR 4,200/month' },
  { id: '2', title: 'Upgrade Refrigerator', description: 'Your refrigerator model is consuming 25% more than average. Consider an upgrade.', estimatedSavings: 'PKR 2,200/month' },
  { id: '3', title: 'Unplug Idle Devices', description: 'The entertainment center shows a constant standby power draw of 50W.', estimatedSavings: 'PKR 1,400/month' },
];

const initialMockDevices: Device[] = [
  { 
    id: 'ac-1', 
    name: 'Living Room AC', 
    status: DeviceStatus.Online, 
    power: 1800, 
    isAdjustable: true, 
    maxPower: 3500,
    normalPowerRange: [1500, 2200],
    tips: [
      "Set thermostat to 24°C instead of 22°C.",
      "Clean filters monthly for max efficiency.",
      "Use a fan to help circulate cool air.",
    ]
  },
  { 
    id: 'fridge-1', 
    name: 'Kitchen Refrigerator', 
    status: DeviceStatus.Online, 
    power: 250, 
    isAdjustable: false,
    normalPowerRange: [150, 300],
    tips: [
      "Ensure door seals are tight and clean.",
      "Don't put hot food directly inside.",
      "Keep it relatively full to maintain cold temps.",
    ]
  },
  { 
    id: 'light-1', 
    name: 'Office Lights', 
    status: DeviceStatus.Idle, 
    power: 10, 
    isAdjustable: true, 
    maxPower: 150,
    normalPowerRange: [80, 120],
    tips: [
      "Switch to energy-efficient LED bulbs.",
      "Use task lighting instead of lighting the whole room.",
      "Turn off lights when you leave the room.",
    ]
  },
  { 
    id: 'pc-1', 
    name: 'Main Computer', 
    status: DeviceStatus.Offline, 
    power: 0, 
    isAdjustable: false,
    normalPowerRange: [200, 450],
    tips: [
      "Use 'Sleep' or 'Hibernate' mode when not in use.",
      "Disable unnecessary startup programs.",
      "Adjust power settings to a 'Power Saver' plan.",
    ]
  },
  {
    id: 'fan-1',
    name: 'Bedroom Ceiling Fan',
    status: DeviceStatus.Idle,
    power: 25,
    isAdjustable: true,
    maxPower: 90,
    normalPowerRange: [25, 75],
    tips: [
      "Use medium speed overnight to keep draw low.",
      "Keep blades clean to reduce drag."
    ]
  },
  {
    id: 'washer-1',
    name: 'Laundry Washer',
    status: DeviceStatus.Offline,
    power: 0,
    isAdjustable: false,
    normalPowerRange: [500, 1500],
    tips: [
      "Run full loads on eco mode whenever possible.",
      "Schedule cycles during off-peak windows."
    ]
  },
  {
    id: 'heater-1',
    name: 'Water Heater',
    status: DeviceStatus.Online,
    power: 1300,
    isAdjustable: false,
    normalPowerRange: [900, 2400],
    tips: [
      "Lower the thermostat a degree or two in summer.",
      "Flush the tank quarterly to remove sediment."
    ]
  },
  {
    id: 'tv-1',
    name: 'Living Room TV',
    status: DeviceStatus.Online,
    power: 180,
    isAdjustable: false,
    normalPowerRange: [120, 220],
    tips: [
      "Enable auto-brightness to reduce peaks.",
      "Turn off connected consoles when idle."
    ]
  },
  {
    id: 'router-1',
    name: 'Wi-Fi Router',
    status: DeviceStatus.Online,
    power: 20,
    isAdjustable: false,
    normalPowerRange: [10, 25],
    tips: [
      "Place the router in an open space for cooling.",
      "Schedule restarts weekly for stability."
    ]
  },
  {
    id: 'microwave-1',
    name: 'Kitchen Microwave',
    status: DeviceStatus.Offline,
    power: 0,
    isAdjustable: false,
    normalPowerRange: [800, 1500],
    tips: [
      "Unplug when not in use to avoid phantom draw.",
      "Use appropriate power levels rather than max."
    ]
  },
];


const buildHistoricalRecords = () => {
  const deviceHistoryMap: PerDeviceHistoricalData = {};
  const unusualEvents: Anomaly[] = [];
  const currentDate = new Date();

  initialMockDevices.forEach(device => {
    const historyPoints: DataPoint[] = [];
    if (!device.normalPowerRange) return;

    for (let dayIndex = 30 * 24 - 1; dayIndex >= 0; dayIndex--) {
      const recordDate = new Date(currentDate.getTime() - dayIndex * 60 * 60 * 1000);
      const [minPower, maxPower] = device.normalPowerRange;
      let recordPower = minPower + Math.random() * (maxPower - minPower);

      if (Math.random() < 0.05) {
        const isAboveNormal = Math.random() > 0.5;
        if (isAboveNormal) {
          recordPower = maxPower * (1.2 + Math.random() * 0.5);
          unusualEvents.push({
            id: `${device.id}-${recordDate.getTime()}`,
            deviceId: device.id,
            deviceName: device.name,
            type: 'high',
            timestamp: recordDate,
            duration: 15 + Math.floor(Math.random() * 45),
            value: parseFloat(recordPower.toFixed(0)),
            normalRange: [minPower, maxPower],
          });
        } else {
          recordPower = minPower * (0.8 - Math.random() * 0.5);
          if (recordPower > 20) {
            unusualEvents.push({
              id: `${device.id}-${recordDate.getTime()}`,
              deviceId: device.id,
              deviceName: device.name,
              type: 'low',
              timestamp: recordDate,
              duration: 15 + Math.floor(Math.random() * 45),
              value: parseFloat(recordPower.toFixed(0)),
              normalRange: [minPower, maxPower],
            });
          }
        }
      }
      
      historyPoints.push({
        date: recordDate,
        time: recordDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        power: parseFloat(recordPower.toFixed(2)),
      });
    }
    deviceHistoryMap[device.id] = historyPoints;
  });

  const combinedData: DataPoint[] = [];
  const uniqueTimes = [...new Set(Object.values(deviceHistoryMap).flat().map(point => point.date.getTime()))].sort();

  uniqueTimes.forEach(timeStamp => {
      const pointDate = new Date(timeStamp);
      let combinedPower = 0;
      Object.values(deviceHistoryMap).forEach(deviceHistory => {
          const matchingPoint = deviceHistory.find(p => p.date.getTime() === timeStamp);
          if (matchingPoint) combinedPower += matchingPoint.power;
      });
      combinedData.push({
          date: pointDate,
          time: pointDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          power: parseFloat(combinedPower.toFixed(2)),
      });
  });
  
  unusualEvents.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

  return { perDeviceData: deviceHistoryMap, totalData: combinedData, anomalies: unusualEvents };
};

const { perDeviceData, totalData, anomalies } = buildHistoricalRecords();

const createStartingData = (): DataPoint[] => {
  const points: DataPoint[] = [];
  const currentTime = new Date();
  currentTime.setHours(currentTime.getHours() - 24);
  
  for (let pointIndex = 0; pointIndex < 96; pointIndex++) {
    const pointTime = new Date(currentTime.getTime() + pointIndex * 15 * 60 * 1000);
    const currentHour = pointTime.getHours();
    
    let powerValue = 1.5;
    powerValue += Math.sin((currentHour - 8) * (Math.PI / 12)) * 1.2;
    powerValue += Math.sin((currentHour - 18) * (Math.PI / 8)) * 1.5;
    powerValue += (Math.random() - 0.5) * 0.5;
    if (powerValue < 0.5) powerValue = 0.5;
    
    points.push({
      date: pointTime,
      time: pointTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      power: parseFloat(powerValue.toFixed(2)),
    });
  }
  return points;
};

const createForecastPoints = (currentData: DataPoint[]): DataPoint[] => {
  return currentData.map(dataPoint => {
    const variation = (Math.random() - 0.5) * 0.2;
    const predictedPower = dataPoint.power * (1 + variation);
    return {
      date: dataPoint.date,
      time: dataPoint.time,
      power: 0,
      forecast: parseFloat(predictedPower.toFixed(2)),
    };
  });
};

const useMockData = () => {
  const [currentData, setCurrentData] = useState<DataPoint[]>(createStartingData());
  const [deviceList, setDeviceList] = useState<Device[]>(initialMockDevices);

  useEffect(() => {
    const updatePowerData = setInterval(() => {
      setCurrentData(oldData => {
        const updatedData = [...oldData];
        const currentTime = new Date();
        const currentHour = currentTime.getHours();
        
        let calculatedPower = 1.5;
        calculatedPower += Math.sin((currentHour - 8) * (Math.PI / 12)) * 1.2;
        calculatedPower += Math.sin((currentHour - 18) * (Math.PI / 8)) * 1.5;
        calculatedPower += (Math.random() - 0.5) * 0.5;
        if (calculatedPower < 0.5) calculatedPower = 0.5;
        
        const latestPoint: DataPoint = {
          date: currentTime,
          time: currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          power: parseFloat(calculatedPower.toFixed(2)),
        };

        return [...updatedData.slice(1), latestPoint];
      });
    }, 5000);

    const updateDeviceStatus = setInterval(() => {
      setDeviceList(oldDevices => {
        const updatedDevices = [...oldDevices];
        const randomIndex = Math.floor(Math.random() * updatedDevices.length);
        const selectedDevice = updatedDevices[randomIndex];
        
        const availableStatuses = Object.values(DeviceStatus).filter(status => status !== selectedDevice.status);
        const randomStatus = availableStatuses[Math.floor(Math.random() * availableStatuses.length)];
        
        let updatedPower = selectedDevice.power;
        if (randomStatus === DeviceStatus.Offline) {
          updatedPower = 0;
        } else if (randomStatus === DeviceStatus.Idle) {
          updatedPower = 10 + Math.random() * 20;
        } else if (randomStatus === DeviceStatus.Online && selectedDevice.status === DeviceStatus.Offline) {
          updatedPower = selectedDevice.normalPowerRange ? selectedDevice.normalPowerRange[0] + 50 : 100;
        }

        updatedDevices[randomIndex] = { ...selectedDevice, status: randomStatus, power: parseFloat(updatedPower.toFixed(0)) };
        return updatedDevices;
      });
    }, 10000);

    return () => {
      clearInterval(updatePowerData);
      clearInterval(updateDeviceStatus);
    };
  }, []);

  const forecastPoints = createForecastPoints(currentData);
  
  const upcomingForecast = useMemo(() => {
    const forecastPoints: DataPoint[] = [];
    const lastPointTime = currentData.length > 0 ? currentData[currentData.length - 1].date : new Date();
    
    for (let forecastIndex = 1; forecastIndex <= 96; forecastIndex++) {
      const forecastTime = new Date(lastPointTime.getTime() + forecastIndex * 15 * 60 * 1000);
      const forecastHour = forecastTime.getHours();
      
      let predictedPower = 1.5;
      predictedPower += Math.sin((forecastHour - 8) * (Math.PI / 12)) * 1.2;
      predictedPower += Math.sin((forecastHour - 18) * (Math.PI / 8)) * 1.5;
      predictedPower += (Math.random() - 0.5) * 0.4;
      if (predictedPower < 0.5) predictedPower = 0.5;
      
      forecastPoints.push({
        date: forecastTime,
        time: forecastTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        power: 0,
        forecast: parseFloat(predictedPower.toFixed(2)),
      });
    }
    return forecastPoints;
  }, [currentData]);

  return { 
    liveData: currentData, 
    forecastData: forecastPoints, 
    recommendations: mockRecommendations, 
    devices: deviceList, 
    historicalData: totalData, 
    perDeviceHistoricalData: perDeviceData, 
    anomalies, 
    futureForecastData: upcomingForecast 
  };
};

export default useMockData;