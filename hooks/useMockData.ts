
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


const generateFullHistoricalData = () => {
  const perDeviceData: PerDeviceHistoricalData = {};
  const anomalies: Anomaly[] = [];
  const now = new Date();

  initialMockDevices.forEach(device => {
    const deviceHistory: DataPoint[] = [];
    if (!device.normalPowerRange) return;

    for (let i = 30 * 24 - 1; i >= 0; i--) { // 30 days of hourly data
      const date = new Date(now.getTime() - i * 60 * 60 * 1000);
      const [min, max] = device.normalPowerRange;
      let power = min + Math.random() * (max - min);

      // Inject anomalies ~5% of the time
      if (Math.random() < 0.05) {
        const isHigh = Math.random() > 0.5;
        if (isHigh) {
          power = max * (1.2 + Math.random() * 0.5); // 20% to 70% higher
          anomalies.push({
            id: `${device.id}-${date.getTime()}`,
            deviceId: device.id,
            deviceName: device.name,
            type: 'high',
            timestamp: date,
            duration: 15 + Math.floor(Math.random() * 45), // 15-60 mins
            value: parseFloat(power.toFixed(0)),
            normalRange: [min, max],
          });
        } else {
          power = min * (0.8 - Math.random() * 0.5);
          if (power > 20) { // Only log if not effectively idle/off
            anomalies.push({
              id: `${device.id}-${date.getTime()}`,
              deviceId: device.id,
              deviceName: device.name,
              type: 'low',
              timestamp: date,
              duration: 15 + Math.floor(Math.random() * 45),
              value: parseFloat(power.toFixed(0)),
              normalRange: [min, max],
            });
          }
        }
      }
      
      deviceHistory.push({
        date,
        time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        power: parseFloat(power.toFixed(2)),
      });
    }
    perDeviceData[device.id] = deviceHistory;
  });

  const totalData: DataPoint[] = [];
  const allTimestamps = [...new Set(Object.values(perDeviceData).flat().map(p => p.date.getTime()))].sort();

  allTimestamps.forEach(ts => {
      const date = new Date(ts);
      let totalPower = 0;
      Object.values(perDeviceData).forEach(history => {
          const point = history.find(p => p.date.getTime() === ts);
          if (point) totalPower += point.power;
      });
      totalData.push({
          date,
          time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          power: parseFloat(totalPower.toFixed(2)),
      });
  });
  
  anomalies.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

  return { perDeviceData, totalData, anomalies };
};

const { perDeviceData, totalData, anomalies } = generateFullHistoricalData();

const generateInitialData = (): DataPoint[] => {
  const data: DataPoint[] = [];
  const now = new Date();
  now.setHours(now.getHours() - 24);
  for (let i = 0; i < 96; i++) { // 96 points for 24 hours (15-minute intervals)
    const time = new Date(now.getTime() + i * 15 * 60 * 1000);
    const hour = time.getHours();
    
    let power = 1.5 + Math.sin((hour - 8) * (Math.PI / 12)) * 1.2 + Math.sin((hour - 18) * (Math.PI / 8)) * 1.5;
    power += (Math.random() - 0.5) * 0.5;
    power = Math.max(0.5, power);
    
    data.push({
      date: time,
      time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      power: parseFloat(power.toFixed(2)),
    });
  }
  return data;
};

const generateForecastData = (liveData: DataPoint[]): DataPoint[] => {
  return liveData.map(dp => {
    let forecastPower = dp.power * (1 + (Math.random() - 0.5) * 0.2);
    return {
      date: dp.date,
      time: dp.time,
      power: 0,
      forecast: parseFloat(forecastPower.toFixed(2)),
    };
  });
};

const useMockData = () => {
  const [liveData, setLiveData] = useState<DataPoint[]>(generateInitialData());
  const [devices, setDevices] = useState<Device[]>(initialMockDevices);

  useEffect(() => {
    const liveDataInterval = setInterval(() => {
      setLiveData(prevData => {
        const newData = [...prevData];
        
        const now = new Date();
        const hour = now.getHours();
        
        let power = 1.5 + Math.sin((hour - 8) * (Math.PI / 12)) * 1.2 + Math.sin((hour - 18) * (Math.PI / 8)) * 1.5;
        power += (Math.random() - 0.5) * 0.5;
        power = Math.max(0.5, power);
        
        const newPoint: DataPoint = {
          date: now,
          time: now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          power: parseFloat(power.toFixed(2)),
        };

        return [...newData.slice(1), newPoint];
      });
    }, 5000); // Update every 5 seconds

    const deviceStatusInterval = setInterval(() => {
      setDevices(prevDevices => {
        const newDevices = [...prevDevices];
        const deviceIndex = Math.floor(Math.random() * newDevices.length);
        const deviceToUpdate = newDevices[deviceIndex];
        
        const possibleStatuses = Object.values(DeviceStatus).filter(s => s !== deviceToUpdate.status);
        const newStatus = possibleStatuses[Math.floor(Math.random() * possibleStatuses.length)];
        
        let newPower = deviceToUpdate.power;
        if(newStatus === DeviceStatus.Offline) newPower = 0;
        else if (newStatus === DeviceStatus.Idle) newPower = 10 + Math.random() * 20;
        else if (newStatus === DeviceStatus.Online && deviceToUpdate.status === DeviceStatus.Offline) {
            newPower = deviceToUpdate.normalPowerRange ? deviceToUpdate.normalPowerRange[0] + 50 : 100;
        }

        newDevices[deviceIndex] = { ...deviceToUpdate, status: newStatus, power: parseFloat(newPower.toFixed(0)) };
        return newDevices;
      });
    }, 10000); // Change a device status every 10 seconds

    return () => {
      clearInterval(liveDataInterval);
      clearInterval(deviceStatusInterval);
    };
  }, []);

  const forecastData = generateForecastData(liveData);
  
  const futureForecastData = useMemo(() => {
    const data: DataPoint[] = [];
    const lastTimestamp = liveData.length > 0 ? liveData[liveData.length - 1].date : new Date();
    
    for (let i = 1; i <= 96; i++) { // 96 points for next 24 hours
      const time = new Date(lastTimestamp.getTime() + i * 15 * 60 * 1000);
      const hour = time.getHours();
      
      let forecastPower = 1.5 + Math.sin((hour - 8) * (Math.PI / 12)) * 1.2 + Math.sin((hour - 18) * (Math.PI / 8)) * 1.5;
      forecastPower += (Math.random() - 0.5) * 0.4;
      forecastPower = Math.max(0.5, forecastPower);
      
      data.push({
        date: time,
        time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        power: 0,
        forecast: parseFloat(forecastPower.toFixed(2)),
      });
    }
    return data;
  }, [liveData]);


  return { liveData, forecastData, recommendations: mockRecommendations, devices, historicalData: totalData, perDeviceHistoricalData: perDeviceData, anomalies, futureForecastData };
};

export default useMockData;