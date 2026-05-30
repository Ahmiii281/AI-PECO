import React, { useState, useMemo } from 'react';
import { Device, DeviceStatus } from '../types';
import { ChipIcon, LightBulbIcon, CheckCircleIcon, ExclamationCircleIcon, TrashIcon } from './Icons';

interface DeviceCardProps {
  device: Device;
  onToggle: (id: string) => void;
  onPowerChange: (id:string, power: number) => void;
  onDelete: (id: string) => void;
}

const statusStyles: Record<DeviceStatus, { dot: string; text: string }> = {
  [DeviceStatus.Online]: { dot: 'bg-[var(--color-success)]', text: 'text-[var(--color-success)]' },
  [DeviceStatus.Offline]: { dot: 'bg-[var(--color-danger)]', text: 'text-[var(--color-danger)]' },
  [DeviceStatus.Idle]: { dot: 'bg-[var(--color-warning)]', text: 'text-[var(--color-warning)]' },
};

const DeviceCard: React.FC<DeviceCardProps> = ({ device, onToggle, onPowerChange, onDelete }) => {
  const [isTipsVisible, setIsTipsVisible] = useState(false);
  const [confirmationType, setConfirmationType] = useState<'power' | 'delete' | null>(null);
  const isOnline = device.status !== DeviceStatus.Offline;

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onPowerChange(device.id, parseInt(e.target.value, 10));
  };
  
  const handleToggleChange = () => {
    if (isOnline) {
      setConfirmationType('power');
    } else {
      onToggle(device.id);
    }
  };

  const requestDelete = () => {
    setConfirmationType('delete');
  };

  const closeConfirmation = () => setConfirmationType(null);

  const handleConfirmAction = () => {
    if (confirmationType === 'power') {
      onToggle(device.id);
    } else if (confirmationType === 'delete') {
      onDelete(device.id);
    }
    setConfirmationType(null);
  };

  const anomalyInfo = useMemo(() => {
    if (device.status !== DeviceStatus.Online || !device.normalPowerRange) {
      return null;
    }
    const [min, max] = device.normalPowerRange;
    if (device.power > max) {
      return { text: 'High Usage Anomaly', color: 'text-red-500 dark:text-red-400', icon: <ExclamationCircleIcon /> };
    }
    if (device.power < min && device.power > 0) { // power > 0 ensures it's not just idle
      return { text: 'Low Usage Anomaly', color: 'text-yellow-500 dark:text-yellow-400', icon: <ExclamationCircleIcon /> };
    }
    return { text: 'Normal Usage', color: 'text-green-500 dark:text-green-400', icon: <CheckCircleIcon /> };
  }, [device.status, device.power, device.normalPowerRange]);

  const powerColorClass = useMemo(() => {
    if (!isOnline || !anomalyInfo) {
      return isOnline ? 'text-gray-800 dark:text-white' : 'text-gray-500 dark:text-gray-400';
    }
    return anomalyInfo.color;
  }, [anomalyInfo, isOnline]);


  return (
    <>
      <div className="p-6 rounded-xl shadow-lg flex flex-col justify-between space-y-4 transform hover:-translate-y-1 transition-transform duration-300 bg-[var(--color-bg-card)] border border-[var(--color-border-default)]">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div className="flex items-center space-x-4">
            <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--color-bg-secondary)' }}>
              <ChipIcon />
            </div>
            <div>
              <h3 className="text-lg font-bold" style={{ color: 'var(--color-text-primary)' }}>{device.name}</h3>
              <div className="flex items-center mt-1 space-x-2">
                <span className={`h-2.5 w-2.5 rounded-full ${statusStyles[device.status].dot}`}></span>
                <p className={`text-sm font-semibold ${statusStyles[device.status].text}`}>{device.status}</p>
              </div>
               {anomalyInfo && (
                <div className={`flex items-center mt-2 space-x-1.5 text-xs font-medium ${anomalyInfo.color}`}>
                  {anomalyInfo.icon}
                  <span>{anomalyInfo.text}</span>
                </div>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={requestDelete}
              className="focus:outline-none rounded-full p-1"
              style={{ color: 'var(--color-text-secondary)' }}
              aria-label={`Remove ${device.name}`}
            >
              <TrashIcon />
            </button>
            <label htmlFor={`toggle-${device.id}`} className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                id={`toggle-${device.id}`}
                className="sr-only peer"
                checked={isOnline}
                onChange={handleToggleChange}
              />
              <div className="w-11 h-6 rounded-full peer peer-focus:ring-2 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border after:rounded-full after:h-5 after:w-5 after:transition-all" style={{ backgroundColor: 'var(--color-border-default)' }} data-checked-bg="var(--color-accent-primary)"></div>
            </label>
          </div>
        </div>

        {/* Power Info */}
        <div className="text-center">
          <p className={`text-5xl font-mono font-bold transition-colors duration-300 ${powerColorClass}`}>{device.power}<span className="text-2xl" style={{ color: 'var(--color-text-secondary)' }}>W</span></p>
        </div>

        {/* Power Slider */}
        <div className="space-y-2">
          <label htmlFor={`slider-${device.id}`} className="text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>
            Power Level
          </label>
          <input
            id={`slider-${device.id}`}
            type="range"
            min="0"
            max={device.maxPower || 100}
            value={device.power}
            onChange={handleSliderChange}
            disabled={!isOnline || !device.isAdjustable}
            className="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-lg appearance-none cursor-pointer
                       [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[var(--color-accent-primary)]
                       disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>

        {/* Tips Section */}
        {device.tips && device.tips.length > 0 && (
            <div className="border-t pt-4" style={{ borderColor: 'var(--color-border-default)' }}>
            <button
              onClick={() => setIsTipsVisible(!isTipsVisible)}
              className="w-full flex justify-between items-center text-left text-sm font-medium"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              <div className="flex items-center space-x-2">
                <LightBulbIcon />
                <span>Energy Saving Tips</span>
              </div>
              <svg
                className={`w-5 h-5 transition-transform duration-300 ${isTipsVisible ? 'transform rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
              <div className={`transition-all duration-300 ease-in-out overflow-hidden ${isTipsVisible ? 'max-h-40 opacity-100 mt-3' : 'max-h-0 opacity-0'}`}>
              <ul className="list-disc list-inside space-y-1 text-xs pl-2" style={{ color: 'var(--color-text-secondary)' }}>
                {device.tips.map((tip, index) => (
                  <li key={index}>{tip}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
      {confirmationType && (
        <div
            className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50"
            onClick={closeConfirmation}
            aria-modal="true"
            role="dialog"
        >
            <div
                className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 m-4 max-w-sm w-full animate-fade-in-scale"
                onClick={(e) => e.stopPropagation()}
            >
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                  {confirmationType === 'power' ? 'Confirm Action' : 'Remove Device'}
                </h3>
                <p className="mt-2 text-gray-600 dark:text-gray-300">
                    {confirmationType === 'power'
                      ? <>Are you sure you want to turn off the <strong>{device.name}</strong>?</>
                      : <>Remove <strong>{device.name}</strong> from your home setup? You can always add it again later.</>}
                </p>
                <div className="mt-6 flex justify-end space-x-3">
                    <button
                        onClick={closeConfirmation}
                        className="px-4 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 dark:focus:ring-offset-gray-800"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleConfirmAction}
                        className={`px-4 py-2 rounded-md text-sm font-medium text-white ${confirmationType === 'delete' ? 'bg-red-600 hover:bg-red-700' : 'bg-red-600 hover:bg-red-700'} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 dark:focus:ring-offset-gray-800`}
                    >
                        {confirmationType === 'power' ? 'Turn Off' : 'Remove'}
                    </button>
                </div>
            </div>
        </div>
      )}
    </>
  );
};

export default DeviceCard;