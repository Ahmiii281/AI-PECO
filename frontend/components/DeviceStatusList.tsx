
import React from 'react';
import { Device, DeviceStatus } from '../types';
import { ChipIcon } from './Icons';

interface DeviceStatusListProps {
  devices: Device[];
}

const statusColors: Record<DeviceStatus, string> = {
  [DeviceStatus.Online]: 'bg-green-500',
  [DeviceStatus.Offline]: 'bg-red-500',
  [DeviceStatus.Idle]: 'bg-yellow-500',
};

const DeviceStatusList: React.FC<DeviceStatusListProps> = ({ devices }) => {
  return (
    <div className="bg-white dark:bg-gray-700/50 p-6 rounded-xl shadow-lg border border-gray-200 dark:border-transparent">
      <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Device Status</h3>
      <ul className="space-y-4">
        {devices.map(device => (
          <li key={device.id} className="flex items-center justify-between bg-gray-100 dark:bg-gray-600/50 p-3 rounded-lg">
            <div className="flex items-center">
                <div className="text-gray-500 dark:text-gray-400"><ChipIcon /></div>
                <div className="ml-4">
                    <p className="font-semibold text-gray-800 dark:text-white">{device.name}</p>
                    <div className="flex items-center mt-1">
                        <span className={`h-2.5 w-2.5 rounded-full mr-2 ${statusColors[device.status]}`}></span>
                        <p className="text-xs text-gray-600 dark:text-gray-300">{device.status}</p>
                    </div>
                </div>
            </div>
            <p className="font-mono text-lg text-green-600 dark:text-green-400">{device.power > 0 ? `${device.power}W` : '-'}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default DeviceStatusList;