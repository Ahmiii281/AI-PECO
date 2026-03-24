import React, { useState } from 'react';
import { BellIcon, CogIcon, ShieldExclamationIcon, TrashIcon, UserCircleIcon } from './Icons';
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


const defaultProfile = {
  name: '',
  location: '',
  email: '',
  phone: '',
  homeType: 'Apartment',
  occupants: '',
  utilityProvider: '',
  energyGoal: 'Trim evening peaks by 10%',
};

const SettingsView: React.FC = () => {
  const [profile, setProfile] = useState(defaultProfile);
  const [houseNotes, setHouseNotes] = useState('');
  const [profileStatus, setProfileStatus] = useState('');
  const [customDetails, setCustomDetails] = useState<Array<{ id: string; label: string; value: string }>>([
    { id: 'detail-1', label: 'Solar Array', value: '5 kW rooftop, facing south' },
    { id: 'detail-2', label: 'EV Charger', value: 'Level 2, 7.2 kW on dedicated circuit' },
  ]);
  const [customDetailDraft, setCustomDetailDraft] = useState({ label: '', value: '' });
  const [notifications, setNotifications] = useState({
    emailAlerts: true,
    aiRecommendations: true,
    weeklySummary: false,
  });

  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setProfile((prev) => ({ ...prev, [name]: value }));
  };

  const addCustomDetail = () => {
    if (!customDetailDraft.label.trim() || !customDetailDraft.value.trim()) {
      setProfileStatus('Fill in both fields before adding a detail.');
      return;
    }
    setCustomDetails((prev) => [
      ...prev,
      { id: `detail-${Date.now()}`, label: customDetailDraft.label.trim(), value: customDetailDraft.value.trim() },
    ]);
    setCustomDetailDraft({ label: '', value: '' });
    setProfileStatus('');
  };

  const removeCustomDetail = (id: string) => {
    setCustomDetails((prev) => prev.filter((detail) => detail.id !== id));
  };

  const handleSaveProfile = () => {
    setProfileStatus('Profile updated. These preferences only live in your browser for now.');
    setTimeout(() => setProfileStatus(''), 5000);
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
            <input
              type="text"
              name="name"
              id="name"
              value={profile.name}
              onChange={handleProfileChange}
              placeholder="e.g., Amina Tariq"
              className="mt-1 block w-full bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-4 py-2 focus:ring-2 focus:ring-green-500 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="location" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Location / City</label>
            <input
              type="text"
              name="location"
              id="location"
              value={profile.location}
              onChange={handleProfileChange}
              placeholder="e.g., Lahore, Punjab"
              className="mt-1 block w-full bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-4 py-2 focus:ring-2 focus:ring-green-500 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="homeType" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Home Type</label>
            <select
              name="homeType"
              id="homeType"
              value={profile.homeType}
              onChange={handleProfileChange}
              className="mt-1 block w-full bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-4 py-2 focus:ring-2 focus:ring-green-500 focus:outline-none"
            >
              <option value="Apartment">Apartment</option>
              <option value="Single-Family House">Single-Family House</option>
              <option value="Shared Space">Shared Space</option>
              <option value="Office / Studio">Office / Studio</option>
            </select>
          </div>
          <div>
            <label htmlFor="occupants" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Occupants</label>
            <input
              type="text"
              name="occupants"
              id="occupants"
              value={profile.occupants}
              onChange={handleProfileChange}
              placeholder="e.g., 2 adults, 1 toddler"
              className="mt-1 block w-full bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-4 py-2 focus:ring-2 focus:ring-green-500 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Email Address</label>
            <input
              type="email"
              name="email"
              id="email"
              value={profile.email}
              onChange={handleProfileChange}
              placeholder="you@example.com"
              className="mt-1 block w-full bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-4 py-2 focus:ring-2 focus:ring-green-500 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="phone" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Phone Number</label>
            <input
              type="tel"
              name="phone"
              id="phone"
              value={profile.phone}
              onChange={handleProfileChange}
              placeholder="+92 XXX XXXXXXX"
              className="mt-1 block w-full bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-4 py-2 focus:ring-2 focus:ring-green-500 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="utilityProvider" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Utility Provider</label>
            <input
              type="text"
              name="utilityProvider"
              id="utilityProvider"
              value={profile.utilityProvider}
              onChange={handleProfileChange}
              placeholder="e.g., LESCO"
              className="mt-1 block w-full bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-4 py-2 focus:ring-2 focus:ring-green-500 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="energyGoal" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Energy Goal</label>
            <input
              type="text"
              name="energyGoal"
              id="energyGoal"
              value={profile.energyGoal}
              onChange={handleProfileChange}
              placeholder="e.g., Stay under 18 kWh/day"
              className="mt-1 block w-full bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-4 py-2 focus:ring-2 focus:ring-green-500 focus:outline-none"
            />
          </div>
          <div className="md:col-span-2">
            <label htmlFor="houseNotes" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Household Notes</label>
            <textarea
              id="houseNotes"
              name="houseNotes"
              value={houseNotes}
              onChange={(e) => setHouseNotes(e.target.value)}
              placeholder="Add reminders, maintenance schedules, or anything about your setup."
              rows={4}
              className="mt-1 block w-full bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-4 py-2 focus:ring-2 focus:ring-green-500 focus:outline-none"
            />
          </div>
        </div>

        <div className="border-t border-gray-200 dark:border-gray-600 mt-6 pt-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-gray-700 dark:text-gray-200">Custom Details</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Add anything unique: inverter size, backup generator, favorite sensors, etc.</p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
              <input
                type="text"
                placeholder="Label"
                value={customDetailDraft.label}
                onChange={(e) => setCustomDetailDraft((prev) => ({ ...prev, label: e.target.value }))}
                className="flex-1 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-green-500 focus:outline-none"
              />
              <input
                type="text"
                placeholder="Value"
                value={customDetailDraft.value}
                onChange={(e) => setCustomDetailDraft((prev) => ({ ...prev, value: e.target.value }))}
                className="flex-1 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-green-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={addCustomDetail}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-semibold rounded-md"
              >
                Add
              </button>
            </div>
          </div>
          <div className="mt-4 space-y-3">
            {customDetails.length === 0 && (
              <p className="text-sm text-gray-500 dark:text-gray-400">You haven’t added any custom details yet.</p>
            )}
            {customDetails.map((detail) => (
              <div
                key={detail.id}
                className="flex items-center justify-between bg-gray-50 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700 rounded-lg px-4 py-2 text-sm"
              >
                <div>
                  <p className="font-semibold text-gray-800 dark:text-gray-100">{detail.label}</p>
                  <p className="text-gray-600 dark:text-gray-300">{detail.value}</p>
                </div>
                <button
                  onClick={() => removeCustomDetail(detail.id)}
                  className="text-gray-400 hover:text-red-500 p-1 rounded-full focus:outline-none focus:ring focus:ring-red-500"
                  aria-label={`Remove ${detail.label}`}
                >
                  <TrashIcon />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mt-6">
          <div className="text-sm text-gray-500 dark:text-gray-400 min-h-[1.5rem]">{profileStatus}</div>
          <button
            onClick={handleSaveProfile}
            className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded-md transition-colors"
          >
            Save Changes
          </button>
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