import React from 'react';
import { 
  ShieldAlert, 
  FileCheck2, 
  Search, 
  FolderKanban, 
  FileText, 
  Sliders, 
  LogOut, 
  Activity, 
  UserCheck, 
  AlertTriangle 
} from 'lucide-react';
import { User } from '../types';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  currentUser: User | null;
  onLogout: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  currentUser,
  onLogout
}) => {
  const menuItems = [
    { id: 'dashboard', label: 'Command Center', icon: Activity },
    { id: 'screening', label: 'Document Screening', icon: FileCheck2 },
    { id: 'cases', label: 'Case Management', icon: FolderKanban },
    { id: 'review_queue', label: 'Alerts & Review Queue', icon: AlertTriangle },
    { id: 'osint', label: 'OSINT Intelligence', icon: Search },
    { id: 'face_verify', label: 'Biometric Verification', icon: UserCheck },
    { id: 'reports', label: 'Screening Reports', icon: FileText },
    { id: 'audit', label: 'Audit & System Admin', icon: Sliders },
  ];

  return (
    <aside className="w-64 bg-navy-900 border-r border-slate-800 flex flex-col justify-between h-screen fixed left-0 top-0 select-none z-20">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-800 flex items-center space-x-3 bg-navy-950">
          <div className="w-9 h-9 rounded-lg bg-sky-600/20 border border-sky-500/40 flex items-center justify-center text-sky-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-wide">IDShield AI</h1>
            <p className="text-xs text-sky-400 font-mono">SEC-SCREEN v1.0</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-sky-600/20 text-sky-300 border border-sky-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-slate-500'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* User profile & session logout */}
      <div className="p-4 border-t border-slate-800 bg-navy-950/70">
        <div className="flex items-center justify-between mb-3">
          <div className="truncate">
            <p className="text-xs font-semibold text-slate-200 truncate">{currentUser?.full_name || 'Officer'}</p>
            <p className="text-[11px] text-sky-400 uppercase font-mono tracking-wider">{currentUser?.role || 'authorized'}</p>
          </div>
          <button
            onClick={onLogout}
            title="Log out"
            className="p-1.5 rounded-md hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
        <div className="flex items-center space-x-2 text-[10px] text-emerald-400 font-mono">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>GATEWAY: CONNECTED</span>
        </div>
      </div>
    </aside>
  );
};
