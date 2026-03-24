
import React, { useEffect, useState } from 'react';
import ThemeToggle from './ThemeToggle';
import { MenuIcon } from './Icons';
import { healthAPI } from '../services/api';

interface HeaderProps {
  onMenuClick: () => void;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let isMounted = true;
    const checkHealth = async () => {
      try {
        const res = await healthAPI.check();
        if (!isMounted) return;
        setBackendOnline(res && res.status === 'healthy');
      } catch {
        if (isMounted) setBackendOnline(false);
      }
    };
    checkHealth();
    const id = window.setInterval(checkHealth, 30000);
    return () => {
      isMounted = false;
      window.clearInterval(id);
    };
  }, []);
  return (
    <header className="bg-white dark:bg-gray-900 shadow-md p-4 flex justify-between items-center z-10 border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center">
        <button
          onClick={onMenuClick}
          className="md:hidden mr-4 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white focus:outline-none focus:ring-2 focus:ring-inset focus:ring-green-500"
          aria-label="Open sidebar"
        >
          <span className="sr-only">Open sidebar</span>
          <MenuIcon />
        </button>
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-800 dark:text-white">AI-PECO Dashboard</h1>
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">AI-Powered Energy Consumption Optimizer</p>
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <div className="hidden sm:flex flex-col items-end text-right text-sm text-gray-500 dark:text-gray-400 space-y-1">
          <div>
            <p>University of Mianwali</p>
            <p>FYP 2025</p>
          </div>
          <div className="flex items-center space-x-2 text-xs">
            <span
              className={`inline-flex h-2.5 w-2.5 rounded-full ${
                backendOnline === null
                  ? 'bg-gray-400'
                  : backendOnline
                  ? 'bg-green-500'
                  : 'bg-red-500'
              }`}
            />
            <span>
              Backend{' '}
              {backendOnline === null
                ? 'checking...'
                : backendOnline
                ? 'online'
                : 'offline'}
            </span>
          </div>
        </div>
        <ThemeToggle />
      </div>
    </header>
  );
};

export default Header;