import { useCallback, useEffect, useRef, useState } from 'react';
import { Device, DeviceStatus, Notification } from '../types';

const getStatusMessage: Record<DeviceStatus, (deviceName: string) => string> = {
  [DeviceStatus.Online]: (name) => `${name} is now online.`,
  [DeviceStatus.Offline]: (name) => `${name} went offline.`,
  [DeviceStatus.Idle]: (name) => `${name} is now idle.`,
};

const getNotificationType: Record<DeviceStatus, Notification['type']> = {
  [DeviceStatus.Online]: 'success',
  [DeviceStatus.Offline]: 'warning',
  [DeviceStatus.Idle]: 'info',
};

const useDeviceNotifications = (devices: Device[]) => {
  const deviceSnapshot = useRef<Map<string, Device> | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const autoHideTimers = useRef<Record<number, ReturnType<typeof setTimeout>>>({});

  const cancelTimer = useCallback((notificationId: number) => {
    if (autoHideTimers.current[notificationId]) {
      clearTimeout(autoHideTimers.current[notificationId]);
      delete autoHideTimers.current[notificationId];
    }
  }, []);

  const removeNotification = useCallback(
    (notificationId: number) => {
      setNotifications((prev) => prev.filter((notif) => notif.id !== notificationId));
      cancelTimer(notificationId);
    },
    [cancelTimer]
  );

  const addNotification = useCallback(
    (message: string, notificationType: Notification['type']) => {
      const notificationId = Date.now();
      setNotifications((prev) => [...prev, { id: notificationId, message, type: notificationType }]);
      autoHideTimers.current[notificationId] = setTimeout(() => removeNotification(notificationId), 5000);
    },
    [removeNotification]
  );

  useEffect(() => {
    if (!deviceSnapshot.current) {
      deviceSnapshot.current = new Map(devices.map((device) => [device.id, device]));
      return;
    }

    const currentSnapshot = new Map(deviceSnapshot.current);

    devices.forEach((device) => {
      const oldDevice = currentSnapshot.get(device.id);
      if (oldDevice && oldDevice.status !== device.status) {
        const messageFunc = getStatusMessage[device.status];
        const notifType = getNotificationType[device.status];
        addNotification(messageFunc(device.name), notifType);
      }
      currentSnapshot.set(device.id, device);
    });

    deviceSnapshot.current = currentSnapshot;
  }, [devices, addNotification]);

  useEffect(() => {
    return () => {
      Object.keys(autoHideTimers.current).forEach((id) => {
        cancelTimer(Number(id));
      });
    };
  }, [cancelTimer]);

  return { notifications, removeNotification };
};

export default useDeviceNotifications;

