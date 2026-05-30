
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
    <header className="p-4 flex justify-between items-center z-10 border-b" style={{ backgroundColor: 'var(--color-bg-secondary)', borderColor: 'var(--color-border-default)' }}>
      <div className="flex items-center">
        <button
          onClick={onMenuClick}
          className="md:hidden mr-4 text-[var(--color-sidebar-text)] hover:text-[var(--color-text-primary)] focus:outline-none"
          aria-label="Open sidebar"
        >
          <span className="sr-only">Open sidebar</span>
          <MenuIcon />
        </button>
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tighter" style={{ color: 'var(--color-text-primary)' }}>AI<span className="" style={{ color: 'var(--color-accent-primary)', margin: '0 4px' }}>-</span>PECO <span className="ml-2 font-mono" style={{ backgroundColor: 'var(--color-accent-glow)', color: 'var(--color-accent-primary)', padding: '0.125rem 0.375rem', borderRadius: '6px', fontSize: '10px' }}>OS_DASHBOARD</span></h1>
          <p className="text-[10px] font-mono uppercase tracking-[0.2em]" style={{ color: 'var(--color-text-secondary)' }}>High Performance Energy Optimization</p>
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <div className="hidden sm:flex flex-col items-end text-right font-mono space-y-1">
          <div className="flex items-center space-x-2 text-[10px] uppercase tracking-widest">
            <span
              style={{
                display: 'inline-block',
                height: '6px',
                width: '6px',
                borderRadius: '999px',
                backgroundColor: backendOnline === null ? 'var(--color-border-subtle)' : backendOnline ? 'var(--color-success)' : 'var(--color-danger)',
                boxShadow: backendOnline ? '0 0 8px rgba(16,185,129,0.18)' : 'none'
              }}
            />
            <span style={{ color: backendOnline ? 'var(--color-success)' : 'var(--color-text-muted)' }}>
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