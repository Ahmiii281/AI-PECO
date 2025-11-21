import React, { useState } from 'react';
// FIX: Import ShieldExclamationIcon to resolve reference error.
import { BellIcon, CogIcon, UserCircleIcon, ShieldExclamationIcon } from './Icons';
import ThemeToggle from './ThemeToggle';

const SettingsCard: React.FC<{ title: string; icon: React.ReactNode; children: React.ReactNode }> = ({ title, icon, children }) => (
  <div className="bg-white dark:bg-gray-700/50 p-6 rounded-xl shadow-lg border border-gray-200 dark:border-transparent">
    <div className="flex items-center mb-4">
      <div className="text-green-500 dark:text-green-400">{icon}</div>
      <h3 className="text-xl font-semibold ml-3 text-gray-900 dark:text-white">{title}</h3>
    </div>
    <div className="space-y-4">{children}</div>
  </div>
);

const ToggleSwitch: React.FC<{ id: string; label: string; enabled: boolean; setEnabled: (enabled: boolean) => void }> = ({ id, label, enabled, setEnabled }) => (
  <div className="flex items-center justify-between">
    <label htmlFor={id} className="text-sm font-medium text-gray-700 dark:text-gray-300">
      {label}
    </label>
    <div className="relative inline-flex items-center cursor-pointer">
      <input type="checkbox" id={id} className="sr-only peer" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
      <div className="w-11 h-6 bg-gray-200 dark:bg-gray-600 rounded-full peer peer-focus:ring-2 peer-focus:ring-green-300 dark:peer-focus:ring-green-800 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
    </div>
  </div>
);


const SettingsView: React.FC = () => {
    const [profile, setProfile] = useState({ name: 'Alex Doe', location: 'Mianwali, Punjab', email: 'alex.doe@university.edu' });
    const [notifications, setNotifications] = useState({
        emailAlerts: true,
        aiRecommendations: true,
        weeklySummary: false
    });

    const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setProfile({ ...profile, [e.target.name]: e.target.value });
    };

  return (
    <div className="p-4 md:p-6 lg:p-8 space-y-8 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white">System Settings</h1>
        <p className="text-md text-gray-500 dark:text-gray-400">Manage your profile, preferences, and application settings.</p>
      </div>

      <SettingsCard title="Profile Information" icon={<UserCircleIcon />}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Full Name</label>
                <input type="text" name="name" id="name" value={profile.name} onChange={handleProfileChange} className="mt-1 block w-full bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-4 py-2 focus:ring-2 focus:ring-green-500 focus:outline-none"/>
            </div>
            <div>
                <label htmlFor="location" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Location / City</label>
                <input type="text" name="location" id="location" value={profile.location} onChange={handleProfileChange} className="mt-1 block w-full bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-4 py-2 focus:ring-2 focus:ring-green-500 focus:outline-none"/>
            </div>
             <div className="md:col-span-2">
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Email Address</label>
                <input type="email" name="email" id="email" value={profile.email} readOnly className="mt-1 block w-full bg-gray-200 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md px-4 py-2 cursor-not-allowed text-gray-500"/>
            </div>
        </div>
        <div className="text-right">
            <button className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded-md transition-colors">Save Changes</button>
        </div>
      </SettingsCard>
      
      <SettingsCard title="Notification Preferences" icon={<BellIcon />}>
        <ToggleSwitch id="email-alerts" label="Email Alerts for Anomalies" enabled={notifications.emailAlerts} setEnabled={(val) => setNotifications(p => ({...p, emailAlerts: val}))} />
        <ToggleSwitch id="ai-recommendations" label="AI-Powered Recommendations" enabled={notifications.aiRecommendations} setEnabled={(val) => setNotifications(p => ({...p, aiRecommendations: val}))} />
        <ToggleSwitch id="weekly-summary" label="Weekly Summary Report" enabled={notifications.weeklySummary} setEnabled={(val) => setNotifications(p => ({...p, weeklySummary: val}))} />
      </SettingsCard>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <SettingsCard title="Appearance" icon={<CogIcon />}>
             <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Interface Theme</p>
                <ThemeToggle />
            </div>
        </SettingsCard>

        <SettingsCard title="Data & Privacy" icon={<ShieldExclamationIcon />}>
            <div className="flex flex-col sm:flex-row gap-3">
                <button className="w-full bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-800 dark:text-white font-bold py-2 px-4 rounded-md transition-colors">
                    Export Consumption Data
                </button>
                 <button className="w-full bg-red-100 dark:bg-red-900/40 hover:bg-red-200 dark:hover:bg-red-900/60 text-red-700 dark:text-red-300 font-bold py-2 px-4 rounded-md transition-colors">
                    Clear Chatbot History
                </button>
            </div>
        </SettingsCard>
      </div>
    </div>
  );
};

export default SettingsView;