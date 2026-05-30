
import React from 'react';
import { Device, DeviceStatus } from '../types';
import { ChipIcon } from './Icons';

interface DeviceStatusListProps {
  devices: Device[];
}

const statusColors: Record<DeviceStatus, string> = {
  [DeviceStatus.Online]: 'bg-[var(--color-success)]',
  [DeviceStatus.Offline]: 'bg-[var(--color-border-subtle)]',
  [DeviceStatus.Idle]: 'bg-[var(--color-text-primary)]',
};

const DeviceStatusList: React.FC<DeviceStatusListProps> = ({ devices }) => {
  return (
    <div className="pcb-card p-6">
      <h3 className="text-xl font-semibold mb-4 font-mono uppercase tracking-tighter" style={{ color: 'var(--color-text-primary)' }}>Inventory <span style={{ color: 'var(--color-accent-primary)' }}>Log</span></h3>
      <ul className="space-y-3">
        {devices.map(device => (
          <li key={device.id} className="flex items-center justify-between p-3 rounded transition-colors" style={{ backgroundColor: 'var(--color-bg-card)', border: '1px solid var(--color-border-default)' }}>
            <div className="flex items-center">
                <div className="text-zinc-600"><ChipIcon /></div>
                <div className="ml-4">
                    <p className="font-semibold text-sm" style={{ color: 'var(--color-text-primary)' }}>{device.name}</p>
                    <div className="flex items-center mt-1">
                        <span className={`h-1.5 w-1.5 rounded-full mr-2 ${statusColors[device.status]}`}></span>
                        <p className="text-[9px] font-mono uppercase tracking-widest" style={{ color: 'var(--color-text-secondary)' }}>{device.status}</p>
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