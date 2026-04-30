
import React from 'react';
import { Device, DeviceStatus } from '../types';
import { ChipIcon } from './Icons';

interface DeviceStatusListProps {
  devices: Device[];
}

const statusColors: Record<DeviceStatus, string> = {
  [DeviceStatus.Online]: 'bg-emerald-500 shadow-[0_0_8px_#00FF41]',
  [DeviceStatus.Offline]: 'bg-zinc-700',
  [DeviceStatus.Idle]: 'bg-white shadow-[0_0_8px_#FFFFFF]',
};

const DeviceStatusList: React.FC<DeviceStatusListProps> = ({ devices }) => {
  return (
    <div className="pcb-card p-6">
      <h3 className="text-xl font-semibold mb-4 text-white font-mono uppercase tracking-tighter">Inventory <span className="text-emerald-500">Log</span></h3>
      <ul className="space-y-3">
        {devices.map(device => (
          <li key={device.id} className="flex items-center justify-between bg-black border border-zinc-900 p-3 rounded hover:border-emerald-500/30 transition-colors">
            <div className="flex items-center">
                <div className="text-zinc-600"><ChipIcon /></div>
                <div className="ml-4">
                    <p className="font-semibold text-white text-sm">{device.name}</p>
                    <div className="flex items-center mt-1">
                        <span className={`h-1.5 w-1.5 rounded-full mr-2 ${statusColors[device.status]}`}></span>
                        <p className="text-[9px] font-mono uppercase tracking-widest text-zinc-500">{device.status}</p>
                    </div>
                </div>
            </div>
            <p className="digital-value text-lg">{device.power > 0 ? `${device.power}W` : '0.00W'}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default DeviceStatusList;