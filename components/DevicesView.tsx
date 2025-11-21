
import React, { useMemo, useState } from 'react';
import useMockData from '../hooks/useMockData';
import { Device, DeviceStatus, Notification } from '../types';
import DeviceCard from './DeviceCard';
import NotificationToast from './NotificationToast';

// --- Main View Component ---
const DevicesView: React.FC = () => {
  const { devices: initialDevices } = useMockData();
  const [devices, setDevices] = useState<Device[]>(initialDevices);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const addNotification = (message: string, type: Notification['type']) => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);
  };

  const removeNotification = (id: number) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const handleToggle = (deviceId: string) => {
    const device = devices.find(d => d.id === deviceId);
    if (!device) return;

    const isTurningOn = device.status === DeviceStatus.Offline;
    const message = isTurningOn ? `${device.name} has been turned on.` : `${device.name} has been turned off.`;
    const type = isTurningOn ? 'success' : 'info';
    
    addNotification(message, type);

    setDevices(prevDevices =>
      prevDevices.map(d => {
        if (d.id === deviceId) {
          if (d.status === DeviceStatus.Offline) {
            // Turning ON
            let defaultPower = 100; // A fallback default
            if (d.isAdjustable && d.maxPower) {
              defaultPower = d.maxPower / 2;
            } else if (d.id === 'fridge-1') {
              defaultPower = 250;
            } else if (d.id === 'pc-1') {
              defaultPower = 300;
            }
            return { ...d, status: DeviceStatus.Online, power: defaultPower };
          } else {
            // Turning OFF
            return { ...d, status: DeviceStatus.Offline, power: 0 };
          }
        }
        return d;
      })
    );
  };

  const handlePowerChange = (deviceId: string, newPower: number) => {
    setDevices(prevDevices =>
      prevDevices.map(d => {
        if (d.id === deviceId) {
          let newStatus: DeviceStatus;
          if (newPower === 0) {
            newStatus = DeviceStatus.Offline;
          } else if (newPower < 20) { // Idle threshold
            newStatus = DeviceStatus.Idle;
          } else {
            newStatus = DeviceStatus.Online;
          }
          return { ...d, power: newPower, status: newStatus };
        }
        return d;
      })
    );
  };
  
  const totalPower = useMemo(() => {
    return devices.reduce((sum, device) => sum + device.power, 0);
  }, [devices]);

  return (
    <>
      {/* Notification Area */}
      <div aria-live="assertive" className="fixed inset-0 flex items-end px-4 py-6 pointer-events-none sm:p-6 sm:items-start z-50">
        <div className="w-full flex flex-col items-center space-y-4 sm:items-end">
          {notifications.map((notification) => (
            <NotificationToast
              key={notification.id}
              notification={notification}
              onClose={() => removeNotification(notification.id)}
            />
          ))}
        </div>
      </div>

      <div className="p-4 md:p-6 lg:p-8 space-y-8">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white">Device Control</h1>
            <p className="text-md text-gray-500 dark:text-gray-400">Remotely manage and monitor your devices.</p>
          </div>
          <div className="w-full sm:w-auto text-left sm:text-right">
              <p className="text-lg font-semibold text-gray-500 dark:text-gray-400">Total Live Power</p>
              <p className="text-4xl font-bold text-green-600 dark:text-green-400">{(totalPower / 1000).toFixed(2)} kW</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {devices.map(device => (
            <DeviceCard
              key={device.id}
              device={device}
              onToggle={handleToggle}
              onPowerChange={handlePowerChange}
            />
          ))}
        </div>
      </div>
    </>
  );
};

export default DevicesView;