
import React, { useMemo, useState } from 'react';
import useMockData from '../hooks/useMockData';
import { Device, DeviceStatus, Notification } from '../types';
import DeviceCard from './DeviceCard';
import NotificationToast from './NotificationToast';

type DeviceTemplate = {
  id: string;
  label: string;
  description: string;
  blueprint: Omit<Device, 'id'>;
  allowNameOverride?: boolean;
};

const DEVICE_TEMPLATES: DeviceTemplate[] = [
  {
    id: 'ceiling-fan',
    label: 'Ceiling Fan',
    description: 'Bedroom or living room, 50–75W draw.',
    blueprint: {
      name: 'Ceiling Fan',
      status: DeviceStatus.Idle,
      power: 35,
      isAdjustable: true,
      maxPower: 90,
      normalPowerRange: [30, 75],
      tips: [
        'Use the medium speed unless the room is extremely hot.',
        'Reverse spin in winter to push warm air down.',
      ],
    },
  },
  {
    id: 'washing-machine',
    label: 'Washing Machine',
    description: 'Laundry day spikes between 500–1200W.',
    blueprint: {
      name: 'Laundry Washer',
      status: DeviceStatus.Offline,
      power: 0,
      isAdjustable: false,
      maxPower: 2200,
      normalPowerRange: [500, 1500],
      tips: [
        'Batch full loads instead of multiple small cycles.',
        'Use cold water programs for 60% less energy.',
      ],
    },
  },
  {
    id: 'water-heater',
    label: 'Water Heater',
    description: 'Continuous draw between 1–3 kW.',
    blueprint: {
      name: 'Water Heater',
      status: DeviceStatus.Online,
      power: 1400,
      isAdjustable: false,
      maxPower: 3000,
      normalPowerRange: [1000, 2500],
      tips: [
        'Lower the thermostat to 50 °C when away for a weekend.',
        'Bleed the tank twice a year to remove sediment.',
      ],
    },
  },
  {
    id: 'smart-tv',
    label: 'Smart TV',
    description: 'Living room entertainment hub.',
    blueprint: {
      name: 'Smart TV',
      status: DeviceStatus.Online,
      power: 160,
      isAdjustable: false,
      maxPower: 280,
      normalPowerRange: [120, 220],
      tips: [
        'Enable ambient light mode to reduce peak brightness.',
        'Shut off peripherals (sound bars, consoles) when not in use.',
      ],
    },
  },
  {
    id: 'wifi-router',
    label: 'Wi-Fi Router',
    description: 'Always-on communications draw (~20W).',
    blueprint: {
      name: 'Wi-Fi Router',
      status: DeviceStatus.Online,
      power: 18,
      isAdjustable: false,
      maxPower: 40,
      normalPowerRange: [10, 25],
      tips: [
        'Schedule an overnight reboot once a week for stability.',
        'Place it in an open area to avoid heat build-up.',
      ],
    },
  },
  {
    id: 'dishwasher',
    label: 'Dishwasher',
    description: '900–1800W while washing/drying.',
    blueprint: {
      name: 'Dishwasher',
      status: DeviceStatus.Offline,
      power: 0,
      isAdjustable: false,
      maxPower: 1800,
      normalPowerRange: [800, 1500],
      tips: [
        'Air-dry instead of heated drying to save ~15%.',
        'Only run full racks to maximize each cycle.',
      ],
    },
  },
  {
    id: 'custom',
    label: 'Custom Device',
    description: 'Define your own power profile.',
    blueprint: {
      name: 'Custom Device',
      status: DeviceStatus.Online,
      power: 150,
      isAdjustable: true,
      maxPower: 500,
      normalPowerRange: [75, 200],
      tips: [
        'Track when this device runs most to find shifting opportunities.',
        'Pair it with a smart plug for precise automation and monitoring.',
      ],
    },
    allowNameOverride: true,
  },
];

const customTemplateDefaults = {
  power: 150,
  maxPower: 750,
  isAdjustable: true,
};

// --- Main View Component ---
const DevicesView: React.FC = () => {
  const { devices: initialDevices } = useMockData();
  const [devices, setDevices] = useState<Device[]>(initialDevices);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>(DEVICE_TEMPLATES[0].id);
  const [customName, setCustomName] = useState('');
  const [customPower, setCustomPower] = useState(customTemplateDefaults.power);
  const [customMaxPower, setCustomMaxPower] = useState(customTemplateDefaults.maxPower);
  const [customAdjustable, setCustomAdjustable] = useState(customTemplateDefaults.isAdjustable);
  const [formError, setFormError] = useState('');

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
    setDevices(prevDevices => {
      const device = prevDevices.find(d => d.id === deviceId);
      if (!device) return prevDevices;
      addNotification(`${device.name} removed from your dashboard.`, 'info');
      return prevDevices.filter(d => d.id !== deviceId);
    });
  };

  const selectedTemplate = DEVICE_TEMPLATES.find(template => template.id === selectedTemplateId) ?? DEVICE_TEMPLATES[0];
  const isCustomTemplate = selectedTemplate.id === 'custom';

  const handleTemplateChange = (templateId: string) => {
    setSelectedTemplateId(templateId);
    setFormError('');
    if (templateId !== 'custom') {
      setCustomName('');
    } else {
      setCustomPower(customTemplateDefaults.power);
      setCustomMaxPower(customTemplateDefaults.maxPower);
      setCustomAdjustable(customTemplateDefaults.isAdjustable);
    }
  };

  const handleAddDevice = () => {
    const template = DEVICE_TEMPLATES.find(t => t.id === selectedTemplateId);
    if (!template) return;

    const effectiveName = (customName || template.blueprint.name).trim();
    if (!effectiveName) {
      setFormError('Please provide a device name.');
      return;
    }

    const baseBlueprint = template.blueprint;
    const timestampId = `user-${Date.now()}`;

    let blueprintToUse: Omit<Device, 'id'> = baseBlueprint;

    if (template.id === 'custom') {
      const safePower = Math.max(0, customPower);
      const safeMax = Math.max(safePower, customMaxPower);
      blueprintToUse = {
        ...baseBlueprint,
        power: safePower,
        maxPower: safeMax,
        isAdjustable: customAdjustable,
        status: safePower === 0 ? DeviceStatus.Offline : DeviceStatus.Online,
        normalPowerRange: [Math.max(5, Math.round(safePower * 0.6)), Math.max(10, Math.round(safePower * 1.2))],
      };
    }

    const deviceToAdd: Device = {
      ...blueprintToUse,
      id: timestampId,
      name: effectiveName,
      tips: blueprintToUse.tips ? [...blueprintToUse.tips] : undefined,
      normalPowerRange: blueprintToUse.normalPowerRange
        ? [...blueprintToUse.normalPowerRange] as [number, number]
        : undefined,
    };

    setDevices(prev => [...prev, deviceToAdd]);
    addNotification(`${effectiveName} added to your home.`, 'success');
    setCustomName('');
    setFormError('');
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
        <div className="bg-white dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700 rounded-2xl p-6 space-y-4 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Household library</p>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Add a device</h2>
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Mirror your actual home by selecting common appliances or defining a custom profile.
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label htmlFor="device-template" className="text-sm font-medium text-gray-700 dark:text-gray-200">Template</label>
              <select
                id="device-template"
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900/50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                value={selectedTemplateId}
                onChange={(e) => handleTemplateChange(e.target.value)}
              >
                {DEVICE_TEMPLATES.map(template => (
                  <option key={template.id} value={template.id}>
                    {template.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 dark:text-gray-400">{selectedTemplate.description}</p>
            </div>
            <div className="space-y-2">
              <label htmlFor="device-name" className="text-sm font-medium text-gray-700 dark:text-gray-200">Display name</label>
              <input
                id="device-name"
                type="text"
                value={customName}
                placeholder={selectedTemplate.blueprint.name}
                onChange={(e) => setCustomName(e.target.value)}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900/50 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>
          </div>
          {isCustomTemplate && (
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-200">Power draw (W)</label>
                <input
                  type="range"
                  min={0}
                  max={3000}
                  value={customPower}
                  onChange={(e) => setCustomPower(parseInt(e.target.value, 10))}
                  className="w-full mt-2"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{customPower} W when active</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-200">Max power (W)</label>
                <input
                  type="range"
                  min={Math.max(customPower, 100)}
                  max={4000}
                  value={customMaxPower}
                  onChange={(e) => setCustomMaxPower(parseInt(e.target.value, 10))}
                  className="w-full mt-2"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{customMaxPower} W ceiling</p>
              </div>
              <div className="flex items-center space-x-3 mt-6 md:mt-8">
                <input
                  id="custom-adjustable"
                  type="checkbox"
                  checked={customAdjustable}
                  onChange={(e) => setCustomAdjustable(e.target.checked)}
                  className="h-4 w-4 text-green-600 border-gray-300 rounded"
                />
                <label htmlFor="custom-adjustable" className="text-sm text-gray-700 dark:text-gray-200">
                  Adjustable via slider
                </label>
              </div>
            </div>
          )}
          {formError && <p className="text-sm text-red-500 dark:text-red-400">{formError}</p>}
          <div className="flex justify-end">
            <button
              onClick={handleAddDevice}
              className="inline-flex items-center px-5 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-semibold transition-colors"
            >
              Add Device
            </button>
          </div>
        </div>
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
      </div>
    </>
  );
};

export default DevicesView;