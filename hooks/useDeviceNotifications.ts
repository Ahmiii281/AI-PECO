import { useCallback, useEffect, useRef, useState } from 'react';
import { Device, DeviceStatus, Notification } from '../types';

const STATUS_COPY: Record<DeviceStatus, (deviceName: string) => string> = {
  [DeviceStatus.Online]: (name) => `${name} is now online.`,
  [DeviceStatus.Offline]: (name) => `${name} went offline.`,
  [DeviceStatus.Idle]: (name) => `${name} is now idle.`,
};

const STATUS_TONE: Record<DeviceStatus, Notification['type']> = {
  [DeviceStatus.Online]: 'success',
  [DeviceStatus.Offline]: 'warning',
  [DeviceStatus.Idle]: 'info',
};

const useDeviceNotifications = (devices: Device[]) => {
  const previousDevices = useRef<Map<string, Device> | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const dismissalTimers = useRef<Record<number, ReturnType<typeof setTimeout>>>({});

  const clearTimer = useCallback((id: number) => {
    if (dismissalTimers.current[id]) {
      clearTimeout(dismissalTimers.current[id]);
      delete dismissalTimers.current[id];
    }
  }, []);

  const removeNotification = useCallback(
    (id: number) => {
      setNotifications((prev) => prev.filter((notification) => notification.id !== id));
      clearTimer(id);
    },
    [clearTimer]
  );

  const pushNotification = useCallback(
    (message: string, type: Notification['type']) => {
      const id = Date.now();
      setNotifications((prev) => [...prev, { id, message, type }]);
      dismissalTimers.current[id] = setTimeout(() => removeNotification(id), 5000);
    },
    [removeNotification]
  );

  useEffect(() => {
    if (!previousDevices.current) {
      previousDevices.current = new Map(devices.map((device) => [device.id, device]));
      return;
    }

    const snapshot = new Map(previousDevices.current);

    devices.forEach((device) => {
      const previous = snapshot.get(device.id);
      if (previous && previous.status !== device.status) {
        const messageFactory = STATUS_COPY[device.status];
        const tone = STATUS_TONE[device.status];
        pushNotification(messageFactory(device.name), tone);
      }
      snapshot.set(device.id, device);
    });

    previousDevices.current = snapshot;
  }, [devices, pushNotification]);

  useEffect(() => {
    return () => {
      Object.keys(dismissalTimers.current).forEach((id) => {
        clearTimer(Number(id));
      });
    };
  }, [clearTimer]);

  return { notifications, removeNotification };
};

export default useDeviceNotifications;

