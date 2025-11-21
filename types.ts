
export enum DeviceStatus {
  Online = 'Online',
  Offline = 'Offline',
  Idle = 'Idle',
}

export type View = 'dashboard' | 'chatbot' | 'devices' | 'reports' | 'settings';

export interface Device {
  id: string;
  name: string;
  status: DeviceStatus;
  power: number; // in Watts
  isAdjustable?: boolean;
  maxPower?: number;
  tips?: string[];
  normalPowerRange?: [number, number];
}

export interface DataPoint {
  date: Date;
  time: string;
  power: number; // in kW
  forecast?: number;
}

export interface Recommendation {
  id:string;
  title: string;
  description: string;
  estimatedSavings: string;
}

export interface Alert {
  id: string;
  message: string;
  timestamp: string;
  severity: 'high' | 'medium' | 'low';
}

export interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'bot';
}

export type NotificationTone = 'success' | 'info' | 'warning';

export interface Notification {
  id: number;
  message: string;
  type: NotificationTone;
}

export type PerDeviceHistoricalData = Record<string, DataPoint[]>;

export interface Anomaly {
  id: string;
  deviceId: string;
  deviceName: string;
  type: 'high' | 'low';
  timestamp: Date;
  duration: number; // in minutes
  value: number; // the anomalous power value
  normalRange: [number, number];
}
