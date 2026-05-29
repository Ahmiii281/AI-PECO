import { Device, DeviceStatus } from '../types';

export type DeviceTemplate = {
  id: string;
  label: string;
  description: string;
  blueprint: Omit<Device, 'id'>;
  allowNameOverride?: boolean;
};

export const DEVICE_TEMPLATES: DeviceTemplate[] = [
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

export const customTemplateDefaults = {
  power: 150,
  maxPower: 750,
  isAdjustable: true,
};
