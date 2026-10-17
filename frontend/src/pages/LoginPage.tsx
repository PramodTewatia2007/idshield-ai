import React, { useState } from 'react';
import { ShieldCheck, Lock, User, KeyRound, AlertCircle } from 'lucide-react';
import { apiClient } from '../api/client';
import { User as UserType } from '../types';

interface LoginModalProps {
  onSuccess: (user: UserType, token: string) => void;
}

export const LoginPage: React.FC<LoginModalProps> = ({ onSuccess }) => {
  const [username, setUsername] = useState('officer');
  const [password, setPassword] = useState('Officer@123456');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const resp = await apiClient.post('/auth/login', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const { access_token, user_info } = resp.data;
      localStorage.setItem('idshield_token', access_token);
      localStorage.setItem('idshield_user', JSON.stringify(user_info));
      onSuccess(user_info, access_token);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const setPresetUser = (user: string, pass: string) => {
    setUsername(user);
    setPassword(pass);
  };

  return (
    <div className="min-h-screen bg-navy-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-navy-800 border border-slate-800 rounded-xl shadow-2xl p-8 backdrop-blur-md">
        <div className="text-center mb-8">
          <div className="inline-flex p-3 rounded-2xl bg-sky-500/10 border border-sky-500/30 text-sky-400 mb-3">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-white tracking-wide">IDShield AI Platform</h2>
          <p className="text-xs text-slate-400 mt-1">Authorized Identity & Border Screening Gateway</p>
        </div>

        {error && (
          <div className="mb-5 p-3 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center space-x-2 text-xs text-red-400">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Operator ID / Username</label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full bg-navy-900 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                placeholder="Enter authorized identifier"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Security Passkey</label>
            <div className="relative">
              <KeyRound className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-navy-900 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                placeholder="Enter password"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-2.5 px-4 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium text-sm transition shadow-lg shadow-sky-600/20 flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            <Lock className="w-4 h-4" />
            <span>{loading ? 'Authenticating...' : 'Sign In to Screening Terminal'}</span>
          </button>
        </form>

        {/* Demo Fast Switcher */}
        <div className="mt-8 pt-6 border-t border-slate-800">
          <p className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold mb-2">
            Demonstration Test Accounts
          </p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <button
              type="button"
              onClick={() => setPresetUser('officer', 'Officer@123456')}
              className="px-2 py-1.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-left transition"
            >
              <div className="font-semibold text-sky-400">Border Officer</div>
              <div className="text-[10px] text-slate-400">officer / Officer@123456</div>
            </button>
            <button
              type="button"
              onClick={() => setPresetUser('investigator', 'Investigator@123')}
              className="px-2 py-1.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-left transition"
            >
              <div className="font-semibold text-indigo-400">OSINT Analyst</div>
              <div className="text-[10px] text-slate-400">investigator / Investigator@123</div>
            </button>
            <button
              type="button"
              onClick={() => setPresetUser('supervisor', 'Supervisor@123')}
              className="px-2 py-1.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-left transition"
            >
              <div className="font-semibold text-emerald-400">Supervisor</div>
              <div className="text-[10px] text-slate-400">supervisor / Supervisor@123</div>
            </button>
            <button
              type="button"
              onClick={() => setPresetUser('admin', 'Admin@123456')}
              className="px-2 py-1.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-left transition"
            >
              <div className="font-semibold text-amber-400">SysAdmin / Audit</div>
              <div className="text-[10px] text-slate-400">admin / Admin@123456</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
