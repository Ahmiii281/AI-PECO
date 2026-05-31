
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MenuIcon } from './Icons';
import { healthAPI } from '../services/api';
import authService from '../services/auth';

interface HeaderProps {
  onMenuClick: () => void;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  const navigate = useNavigate();
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(authService.isAuthenticated());

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

    const updateAuth = () => setIsAuthenticated(authService.isAuthenticated());
    authService.subscribe(updateAuth);

    return () => {
      isMounted = false;
      authService.unsubscribe(updateAuth);
      window.clearInterval(id);
    };
  }, []);

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

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
        {isAuthenticated && (
          <button
            onClick={handleLogout}
            className="rounded-md border border-[var(--color-border-default)] bg-[var(--color-bg-card)] px-4 py-2 text-sm font-semibold text-[var(--color-text-primary)] hover:bg-[var(--color-bg-primary)]"
          >
            Logout
          </button>
        )}
      </div>
    </header>
  );
};

export default Header;