import React, { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { apiClient } from '../api/client';

export const AdminAuditPage: React.FC = () => {
  const [audits, setAudits] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAudits = async () => {
    try {
      setLoading(true);
      const resp = await apiClient.get('/audit-events?limit=100');
      setAudits(resp.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    apiClient.get('/audit-events?limit=100').then((resp) => {
      if (isMounted) {
        setAudits(resp.data);
        setLoading(false);
      }
    }).catch((err) => {
      console.error(err);
      if (isMounted) setLoading(false);
    });
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">System Governance & Audit Trail</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Tamper-evident log of all screening actions, OCR corrections, biometric comparisons, and officer adjudications.
          </p>
        </div>
        <button
          onClick={fetchAudits}
          disabled={loading}
          className="px-3 py-1.5 rounded-lg bg-navy-800 border border-slate-700 hover:bg-slate-800 text-xs text-slate-300 flex items-center space-x-1.5 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-sky-400' : ''}`} />
          <span>{loading ? 'Refreshing...' : 'Refresh Trail'}</span>
        </button>
      </div>

      {/* Audit Table */}
      <div className="bg-navy-800 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-700/80 bg-navy-900/60 text-slate-400 uppercase tracking-wider font-mono">
                <th className="py-3 px-4 font-medium">Event ID</th>
                <th className="py-3 px-4 font-medium">Timestamp</th>
                <th className="py-3 px-4 font-medium">Operator / Actor</th>
                <th className="py-3 px-4 font-medium">Action Performed</th>
                <th className="py-3 px-4 font-medium">Resource Ref</th>
                <th className="py-3 px-4 font-medium">IP Address</th>
                <th className="py-3 px-4 font-medium text-right">Outcome</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-slate-300">
              {audits.map((a) => (
                <tr key={a.id} className="hover:bg-slate-800/30 transition">
                  <td className="py-3 px-4 font-mono text-sky-400">#{a.id}</td>
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                    {String(a.timestamp).substring(0, 19).replace('T', ' ')}
                  </td>
                  <td className="py-3 px-4 font-medium text-white">{a.actor_username}</td>
                  <td className="py-3 px-4 font-mono text-[11px]">{a.action}</td>
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                    {a.resource_type}:{a.resource_id}
                  </td>
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-400">{a.ip_address}</td>
                  <td className="py-3 px-4 text-right">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      {a.outcome}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
