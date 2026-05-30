
import React, { useEffect, useMemo, useState } from 'react';
import useMockData from '../hooks/useMockData';
import { BackendDevice, Device, DeviceStatus, Notification } from '../types';
import DeviceCard from './DeviceCard';
import NotificationToast from './NotificationToast';
import { deviceAPI, dashboardAPI } from '../services/api';
import authService from '../services/auth';
import { USE_DEMO_DATA } from '../demoConfig';

import { DEVICE_TEMPLATES, DeviceTemplate } from './DeviceTemplates';
import AddDeviceCard from './AddDeviceCard';

// --- Main View Component ---
const DevicesView: React.FC = () => {
  const isDemoMode = USE_DEMO_DATA;
  const { devices: initialDevices } = useMockData();
  const [devices, setDevices] = useState<Device[]>(initialDevices);
  const [isBackendMode, setIsBackendMode] = useState(false);
  const [isLoadingBackend, setIsLoadingBackend] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    let isMounted = true;

    const loadBackendDevices = async () => {
      if (!authService.isAuthenticated()) return;
      setIsLoadingBackend(true);
      setLoadError(null);
      try {
        const backendDevices = await deviceAPI.getAll() as BackendDevice[];
        if (!isMounted) return;

        const mappedDevices: Device[] = backendDevices.map((d) => {
          const status = String(d.status || '').toLowerCase();
          let mappedStatus = DeviceStatus.Offline;
          if (status === 'online') mappedStatus = DeviceStatus.Online;
          else if (status === 'idle') mappedStatus = DeviceStatus.Idle;
          return {
            id: d.id,
            name: d.name,
            status: mappedStatus,
            power: 0,
            isAdjustable: true,
            maxPower: 2000,
            tips: [`Backend device at ${d.location}`, `Relay pin: ${d.relay_pin}`],
          };
        });

        setDevices(mappedDevices.length ? mappedDevices : initialDevices);
        setIsBackendMode(mappedDevices.length > 0);
      } catch (error: unknown) {
        const msg = error instanceof Error ? error.message : 'Failed to load devices.';
        console.error('Failed to load devices from backend', error);
        if (isMounted) {
          setLoadError(msg);
          setIsBackendMode(false);
        }
      } finally {
        if (isMounted) setIsLoadingBackend(false);
      }
    };

    loadBackendDevices();

    return () => {
      isMounted = false;
    };
  }, [initialDevices]);

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

    if (isBackendMode) {
      const command = isTurningOn ? 'ON' : 'OFF';
      dashboardAPI
        .controlRelay(deviceId, command)
        .catch((error) => {
          console.error('Failed to send relay command', error);
          addNotification('Failed to sync with backend relay. Local state only.', 'warning');
        });
    }

    setDevices(prevDevices =>
      prevDevices.map(d => {
        if (d.id === deviceId) {
          if (d.status === DeviceStatus.Offline) {
            const defaultPower = d.normalPowerRange
              ? Math.round((d.normalPowerRange[0] + d.normalPowerRange[1]) / 2)
              : d.maxPower
                ? Math.round(d.maxPower * 0.6)
                : 100;
            return { ...d, status: DeviceStatus.Online, power: defaultPower };
          } else {
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
  const handleDeleteDevice = (deviceId: string) => {
    if (isBackendMode) {
      deviceAPI
        .delete(deviceId)
        .catch((error) => {
          console.error('Failed to delete device in backend', error);
          addNotification('Backend delete failed, removing from local view only.', 'warning');
        });
    }

    setDevices(prevDevices => {
      const device = prevDevices.find(d => d.id === deviceId);
      if (!device) return prevDevices;
      addNotification(`${device.name} removed from your dashboard.`, 'info');
      return prevDevices.filter(d => d.id !== deviceId);
    });
  };

  const handleAddDevice = (name: string, template: DeviceTemplate, customDetails?: {
    power: number;
    maxPower: number;
    adjustable: boolean;
  }) => {
    const baseBlueprint = template.blueprint;
    const timestampId = `user-${Date.now()}`;

    let blueprintToUse: Omit<Device, 'id'> = baseBlueprint;

    if (template.id === 'custom' && customDetails) {
      const safePower = Math.max(0, customDetails.power);
      const safeMax = Math.max(safePower, customDetails.maxPower);
      blueprintToUse = {
        ...baseBlueprint,
        power: safePower,
        maxPower: safeMax,
        isAdjustable: customDetails.adjustable,
        status: safePower === 0 ? DeviceStatus.Offline : DeviceStatus.Online,
        normalPowerRange: [Math.max(5, Math.round(safePower * 0.6)), Math.max(10, Math.round(safePower * 1.2))],
      };
    }

    const deviceToAdd: Device = {
      ...blueprintToUse,
      id: timestampId,
      name: name,
      tips: blueprintToUse.tips ? [...blueprintToUse.tips] : undefined,
      normalPowerRange: blueprintToUse.normalPowerRange
        ? [...blueprintToUse.normalPowerRange] as [number, number]
        : undefined,
    };

    if (isBackendMode) {
      deviceAPI
        .create(name, 'Home', 26)
        .then((created: BackendDevice) => {
          const createdMapped: Device = {
            ...deviceToAdd,
            id: created.id,
            tips: [`Backend device at ${created.location}`, `Relay pin: ${created.relay_pin}`],
          };
          setDevices(prev => [...prev, createdMapped]);
        })
        .catch((error) => {
          console.error('Failed to create device in backend', error);
          addNotification('Device added locally, but backend sync failed.', 'warning');
          setDevices(prev => [...prev, deviceToAdd]);
        });
    } else {
      setDevices(prev => [...prev, deviceToAdd]);
    }
    addNotification(`${name} added to your home.`, 'success');
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
            <h1 className="text-3xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Device Control</h1>
            <p className="text-md" style={{ color: 'var(--color-text-secondary)' }}>
              Remotely manage and monitor your devices{isDemoMode ? ' using a demo library of sample appliances.' : '.'}
            </p>
          </div>
          <div className="w-full sm:w-auto text-left sm:text-right">
              <p className="text-lg font-semibold" style={{ color: 'var(--color-text-secondary)' }}>
                Total Live Power {isBackendMode && '(backend devices)'}
              </p>
              <p className="text-4xl font-bold" style={{ color: 'var(--color-accent-primary)' }}>{(totalPower / 1000).toFixed(2)} kW</p>
          </div>
        </div>
        <AddDeviceCard onAdd={handleAddDevice} />
        {/* Device loading skeleton */}
        {isLoadingBackend ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6" aria-label="Loading devices">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="rounded-xl h-48 animate-pulse" style={{ backgroundColor: 'var(--color-bg-card-hover)' }} />
            ))}
          </div>
        ) : loadError ? (
          <div className="flex flex-col items-center gap-3 py-12 text-center">
            <p className="font-medium" style={{ color: 'var(--color-warning)' }}>⚠️ {loadError}</p>
            <button
              onClick={() => setIsLoadingBackend(true)}
              className="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              style={{ backgroundColor: 'var(--color-accent-primary)', color: 'black' }}
            >
              Retry
            </button>
            <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>Showing demo devices below.</p>
          </div>
        ) : devices.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-16 text-center">
            <p className="text-lg" style={{ color: 'var(--color-text-secondary)' }}>No devices yet.</p>
            <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>Use the panel above to add your first device.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {devices.map(device => (
              <DeviceCard
                key={device.id}
                device={device}
                onToggle={handleToggle}
                onPowerChange={handlePowerChange}
                onDelete={handleDeleteDevice}
              />
            ))}
          </div>
        )}
      </div>
    </>
  );
};

export default DevicesView;