
import React from 'react';
import { ChartBarIcon, ChipIcon, DocumentReportIcon, CogIcon, VoiceChatIcon, XIcon } from './Icons';
import { View } from '../types';

interface SidebarProps {
  activeView: View;
  setActiveView: (view: View) => void;
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeView, setActiveView, isOpen, setIsOpen }) => {
  const navItems: Array<{ name: string; view: View; icon: React.ReactNode }> = [
    { name: 'Dashboard', view: 'dashboard', icon: <ChartBarIcon /> },
    { name: 'AI Chatbot', view: 'chatbot', icon: <VoiceChatIcon /> },
    { name: 'Devices', view: 'devices', icon: <ChipIcon /> },
    { name: 'Sensor (DHT)', view: 'dht', icon: <SunIcon /> },
    { name: 'Reports', view: 'reports', icon: <DocumentReportIcon /> },
    { name: 'Settings', view: 'settings', icon: <CogIcon /> },
  ];

  const handleItemClick = (view: View) => {
    setActiveView(view);
    setIsOpen(false); // Close sidebar on mobile after navigation
  };

  return (
    <>
      {/* Backdrop for mobile */}
      <div
        className={`fixed inset-0 bg-black bg-opacity-60 z-20 transition-opacity md:hidden ${
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={() => setIsOpen(false)}
        aria-hidden="true"
      ></div>

      {/* Sidebar */}
      <aside className={`fixed top-0 left-0 h-full w-64 bg-white dark:bg-gray-900 text-gray-800 dark:text-white flex-col z-30 transition-transform duration-300 ease-in-out md:flex md:static md:translate-x-0 border-r border-gray-200 dark:border-gray-700 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-3xl font-bold text-green-600 dark:text-green-400">AI-PECO</h2>
          <button
            onClick={() => setIsOpen(false)}
            className="md:hidden text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
            aria-label="Close sidebar"
          >
            <span className="sr-only">Close sidebar</span>
            <XIcon />
          </button>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-2">
          {navItems.map((item) => (
            <button
              key={item.name}
              onClick={() => handleItemClick(item.view)}
              className={`w-full flex items-center px-4 py-3 text-lg rounded-lg transition-colors duration-200 ${
                activeView === item.view
                  ? 'bg-green-500 text-white'
                  : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              {item.icon}
              <span className="ml-4">{item.name}</span>
            </button>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 text-center text-xs text-gray-500 dark:text-gray-500">
          <p>&copy; 2025 AI-PECO Team</p>
          <p>All Rights Reserved</p>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;