import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { dashboardAPI, energyAPI, deviceAPI } from '../../services/api';
import './Dashboard.css';

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [devices, setDevices] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [energyData, setEnergyData] = useState<any[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    if (selectedDevice) {
      loadEnergyData(selectedDevice);
    }
  }, [selectedDevice]);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const [statsData, devicesData, alertsData] = await Promise.all([
        dashboardAPI.getStats(),
        deviceAPI.getAll(),
        energyAPI.getAlerts(false),
      ]);

      setStats(statsData);
      setDevices(devicesData);
      setAlerts(alertsData);

      // Select first device by default
      if (devicesData.length > 0) {
        setSelectedDevice(devicesData[0].id);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadEnergyData = async (deviceId: string) => {
    try {
      const data = await energyAPI.getDeviceHistory(deviceId, 24);
      setEnergyData(data.reverse().slice(0, 50)); // Last 50 readings
    } catch (err: any) {
      console.error('Failed to load energy data:', err);
    }
  };

  const handleRelayToggle = async (deviceId: string, currentState: boolean) => {
    try {
      await dashboardAPI.controlRelay(deviceId, currentState ? 'OFF' : 'ON');
      loadDashboard();
    } catch (err: any) {
      setError('Failed to toggle relay');
    }
  };

  const handleResolveAlert = async (alertId: string) => {
    try {
      await energyAPI.resolveAlert(alertId);
      setAlerts(alerts.filter(a => a.id !== alertId));
    } catch (err: any) {
      setError('Failed to resolve alert');
    }
  };

  if (loading) return <div className="dashboard-container"><p>Loading...</p></div>;

  const powerData = energyData.map(d => ({
    time: new Date(d.timestamp).toLocaleTimeString().slice(0, 5),
    power: Math.round(d.power),
    current: Math.round(d.current * 100) / 100,
  }));

  return (
    <div className="dashboard-container">
      {error && <div className="error-banner">{error}</div>}

      {/* Stats Section */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Power</div>
          <div className="stat-value">{stats?.total_power?.toFixed(0) || 0}W</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Avg Temperature</div>
          <div className="stat-value">{stats?.avg_temperature?.toFixed(1) || 0}°C</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Avg Humidity</div>
          <div className="stat-value">{stats?.avg_humidity?.toFixed(1) || 0}%</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Forecasted Power</div>
          <div className="stat-value">{stats?.forecasted_power?.toFixed(0) || 0}W</div>
        </div>
        <div className="stat-card alert">
          <div className="stat-label">Alerts</div>
          <div className="stat-value">{stats?.alert_count || 0}</div>
        </div>
      </div>

      {/* Devices Section */}
      <div className="devices-section">
        <h2>Devices</h2>
        <div className="devices-grid">
          {devices.map(device => (
            <div
              key={device.id}
              className={`device-card ${selectedDevice === device.id ? 'selected' : ''}`}
              onClick={() => setSelectedDevice(device.id)}
            >
              <div className="device-header">
                <h3>{device.name}</h3>
                <span className={`status ${device.status}`}>{device.status}</span>
              </div>
              <p className="device-location">{device.location}</p>
              <div className="device-controls">
                <button
                  className={`relay-btn ${device.is_relay_on ? 'on' : 'off'}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRelayToggle(device.id, device.is_relay_on);
                  }}
                >
                  Relay: {device.is_relay_on ? 'ON' : 'OFF'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Energy Charts */}
      {selectedDevice && powerData.length > 0 && (
        <div className="charts-section">
          <h2>Energy Consumption (Last 24h)</h2>

          <div className="chart-container">
            <h3>Power Usage</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={powerData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="power" stroke="#667eea" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>Current Draw</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={powerData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="current" fill="#764ba2" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Alerts Section */}
      {alerts.length > 0 && (
        <div className="alerts-section">
          <h2>Active Alerts ({alerts.length})</h2>
          <div className="alerts-list">
            {alerts.map(alert => (
              <div key={alert.id} className={`alert-item ${alert.alert_type}`}>
                <div className="alert-content">
                  <strong>{alert.alert_type.toUpperCase()}</strong>
                  <p>{alert.message}</p>
                  <small>{new Date(alert.created_at).toLocaleString()}</small>
                </div>
                <button
                  className="resolve-btn"
                  onClick={() => handleResolveAlert(alert.id)}
                >
                  Resolve
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
