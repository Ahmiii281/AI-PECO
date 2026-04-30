
import React, { useEffect, useState } from 'react';
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
    <header className="bg-black p-4 flex justify-between items-center z-10 border-b border-zinc-900 shadow-lg">
      <div className="flex items-center">
        <button
          onClick={onMenuClick}
          className="md:hidden mr-4 text-zinc-500 hover:text-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
          aria-label="Open sidebar"
        >
          <span className="sr-only">Open sidebar</span>
          <MenuIcon />
        </button>
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tighter">AI<span className="text-emerald-500">-</span>PECO <span className="text-[10px] bg-emerald-500/10 text-emerald-500 px-1.5 py-0.5 rounded ml-2 font-mono">OS_DASHBOARD</span></h1>
          <p className="text-[10px] text-zinc-500 font-mono uppercase tracking-[0.2em]">High Performance Energy Optimization</p>
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <div className="hidden sm:flex flex-col items-end text-right font-mono space-y-1">
          <div className="flex items-center space-x-2 text-[10px] uppercase tracking-widest">
            <span
              className={`inline-flex h-1.5 w-1.5 rounded-full ${
                backendOnline === null
                  ? 'bg-zinc-700'
                  : backendOnline
                  ? 'bg-emerald-500 shadow-[0_0_10px_#00FF41] animate-pulse'
                  : 'bg-red-600'
              }`}
            />
            <span className={backendOnline ? 'text-emerald-500' : 'text-zinc-600'}>
              SYS_{' '}
              {backendOnline === null
                ? 'BOOTING'
                : backendOnline
                ? 'ONLINE'
                : 'OFFLINE'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;