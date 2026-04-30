
import React from 'react';
import { ChartBarIcon, ChipIcon, DocumentReportIcon, CogIcon, VoiceChatIcon, XIcon, SunIcon, CalculatorIcon } from './Icons';
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
    { name: 'Bill Estimation', view: 'billing', icon: <CalculatorIcon /> },
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
      <aside className={`fixed top-0 left-0 h-full w-64 bg-black text-white flex-col z-30 transition-transform duration-300 ease-in-out md:flex md:static md:translate-x-0 border-r border-zinc-900 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center justify-between p-6 border-b border-zinc-900">
          <h2 className="text-3xl font-bold text-emerald-500 tracking-tighter">
            AI<span className="text-white">-</span>PECO
          </h2>
          <button
            onClick={() => setIsOpen(false)}
            className="md:hidden text-zinc-500 hover:text-white"
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
              className={`w-full flex items-center px-4 py-3 text-lg rounded transition-all duration-200 ${
                activeView === item.view
                  ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 font-bold'
                  : 'text-zinc-500 hover:bg-zinc-900 hover:text-white'
              }`}
            >
              <div className={activeView === item.view ? 'text-emerald-500' : 'text-zinc-600'}>
                {item.icon}
              </div>
              <span className="ml-4">{item.name}</span>
            </button>
          ))}
        </nav>
        <div className="p-4 border-t border-zinc-900 text-center text-[10px] uppercase tracking-widest text-zinc-600 font-mono">
          <p>&copy; 2025 AI-PECO SYSTEMS</p>
          <p>BUILD_REL_STABLE</p>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;