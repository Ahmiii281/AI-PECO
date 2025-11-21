import React, { useState, useMemo } from 'react';
import { Device, DeviceStatus } from '../types';
import { ChipIcon, LightBulbIcon, CheckCircleIcon, ExclamationCircleIcon } from './Icons';

interface DeviceCardProps {
  device: Device;
  onToggle: (id: string) => void;
  onPowerChange: (id:string, power: number) => void;
}

const statusStyles: Record<DeviceStatus, { dot: string; text: string }> = {
  [DeviceStatus.Online]: { dot: 'bg-green-500', text: 'text-green-500 dark:text-green-400' },
  [DeviceStatus.Offline]: { dot: 'bg-red-500', text: 'text-red-500 dark:text-red-400' },
  [DeviceStatus.Idle]: { dot: 'bg-yellow-500', text: 'text-yellow-500 dark:text-yellow-400' },
};

const DeviceCard: React.FC<DeviceCardProps> = ({ device, onToggle, onPowerChange }) => {
  const [isTipsVisible, setIsTipsVisible] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const isOnline = device.status !== DeviceStatus.Offline;

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onPowerChange(device.id, parseInt(e.target.value, 10));
  };
  
  const handleToggleChange = () => {
    if (isOnline) {
      // If device is on, show confirmation to turn off
      setShowConfirmation(true);
    } else {
      // If device is off, turn on immediately
      onToggle(device.id);
    }
  };

  const handleConfirmTurnOff = () => {
    onToggle(device.id);
    setShowConfirmation(false);
  };
  
  const handleCancelTurnOff = () => {
    setShowConfirmation(false);
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
      <div className="bg-white dark:bg-gray-700/50 p-6 rounded-xl shadow-lg border border-gray-200 dark:border-transparent flex flex-col justify-between space-y-4 transform hover:-translate-y-1 transition-transform duration-300">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
              <ChipIcon />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">{device.name}</h3>
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
          <label htmlFor={`toggle-${device.id}`} className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              id={`toggle-${device.id}`}
              className="sr-only peer"
              checked={isOnline}
              onChange={handleToggleChange}
            />
            <div className="w-11 h-6 bg-gray-200 dark:bg-gray-600 rounded-full peer peer-focus:ring-2 peer-focus:ring-green-300 dark:peer-focus:ring-green-800 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
          </label>
        </div>

        {/* Power Info */}
        <div className="text-center">
          <p className={`text-5xl font-mono font-bold transition-colors duration-300 ${powerColorClass}`}>{device.power}<span className="text-2xl text-gray-500 dark:text-gray-400">W</span></p>
        </div>

        {/* Power Slider */}
        <div className="space-y-2">
          <label htmlFor={`slider-${device.id}`} className="text-sm font-medium text-gray-500 dark:text-gray-400">
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
                       [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-green-600
                       disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>

        {/* Tips Section */}
        {device.tips && device.tips.length > 0 && (
          <div className="border-t border-gray-200 dark:border-gray-600 pt-4">
            <button
              onClick={() => setIsTipsVisible(!isTipsVisible)}
              className="w-full flex justify-between items-center text-left text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
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
              <ul className="list-disc list-inside space-y-1 text-xs text-gray-500 dark:text-gray-400 pl-2">
                {device.tips.map((tip, index) => (
                  <li key={index}>{tip}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
      {showConfirmation && (
        <div
            className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50"
            onClick={handleCancelTurnOff}
            aria-modal="true"
            role="dialog"
        >
            <div
                className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 m-4 max-w-sm w-full animate-fade-in-scale"
                onClick={(e) => e.stopPropagation()}
            >
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">Confirm Action</h3>
                <p className="mt-2 text-gray-600 dark:text-gray-300">
                    Are you sure you want to turn off the <strong>{device.name}</strong>?
                </p>
                <div className="mt-6 flex justify-end space-x-3">
                    <button
                        onClick={handleCancelTurnOff}
                        className="px-4 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 dark:focus:ring-offset-gray-800"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleConfirmTurnOff}
                        className="px-4 py-2 rounded-md text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 dark:focus:ring-offset-gray-800"
                    >
                        Turn Off
                    </button>
                </div>
            </div>
        </div>
      )}
    </>
  );
};

export default DeviceCard;