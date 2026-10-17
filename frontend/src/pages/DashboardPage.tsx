import React, { useEffect, useState } from 'react';
import { 
  FileCheck2, 
  AlertTriangle, 
  FolderClock, 
  Search, 
  Cpu, 
  RefreshCw 
} from 'lucide-react';
import { apiClient } from '../api/client';
import { DashboardMetrics } from '../types';

export const DashboardPage: React.FC<{ onNavigateToCase: (id: number) => void }> = ({ onNavigateToCase }) => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const resp = await apiClient.get('/dashboard/metrics');
      setMetrics(resp.data);
    } catch (err) {
      console.error('Failed to load metrics', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    apiClient.get('/dashboard/metrics').then((resp) => {
      if (isMounted) {
        setMetrics(resp.data);
        setLoading(false);
      }
    }).catch((err) => {
      console.error('Failed to load metrics', err);
      if (isMounted) setLoading(false);
    });
    return () => {
      isMounted = false;
    };
  }, []);

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        <RefreshCw className="w-6 h-6 animate-spin text-sky-500 mr-2" />
        <span>Loading operational telemetry...</span>
      </div>
    );
  }

  const statCards = [
    {
      label: 'Documents Processed',
      value: metrics?.documents_processed || 0,
      icon: FileCheck2,
      color: 'text-sky-400',
      bg: 'bg-sky-500/10 border-sky-500/20',
      detail: 'Cumulative verified docs'
    },
    {
      label: 'Cases Awaiting Review',
      value: metrics?.cases_awaiting_review || 0,
      icon: FolderClock,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20',
      detail: 'Requires officer adjudication'
    },
    {
      label: 'Forensic Tampering Alerts',
      value: metrics?.potential_anomalies || 0,
      icon: AlertTriangle,
      color: 'text-red-400',
      bg: 'bg-red-500/10 border-red-500/20',
      detail: 'Physical / digital anomalies'
    },
    {
      label: 'OSINT Corroborations',
      value: metrics?.osint_investigations || 0,
      icon: Search,
      color: 'text-indigo-400',
      bg: 'bg-indigo-500/10 border-indigo-500/20',
      detail: 'Cross-registry intelligence'
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">Operational Command Center</h2>
          <p className="text-xs text-slate-400 mt-0.5">Real-time border screening telemetry, queue status & integration health</p>
        </div>
        <button
          onClick={fetchMetrics}
          className="px-3 py-1.5 rounded-lg bg-navy-800 border border-slate-700 hover:bg-slate-800 text-xs text-slate-300 flex items-center space-x-1.5 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <div key={i} className={`p-4 rounded-xl border ${card.bg} bg-navy-800 backdrop-blur-sm`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-slate-300">{card.label}</span>
                <Icon className={`w-5 h-5 ${card.color}`} />
              </div>
              <div className="text-2xl font-bold text-white">{card.value}</div>
              <div className="text-[11px] text-slate-400 mt-1 flex items-center">
                <span>{card.detail}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Dual Section: System Integration Grid & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Integration Availability Matrix */}
        <div className="lg:col-span-1 bg-navy-800 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center space-x-2 mb-4">
            <Cpu className="w-4 h-4 text-sky-400" />
            <h3 className="text-sm font-semibold text-white">Integration & Pipeline Status</h3>
          </div>
          <div className="space-y-3">
            {metrics?.integration_status && Object.entries(metrics.integration_status).map(([svc, status], idx) => {
              const isOk = status.includes('operational');
              return (
                <div key={idx} className="flex items-center justify-between text-xs py-1.5 border-b border-slate-800/60 last:border-0">
                  <span className="text-slate-300 truncate pr-2">{svc}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${
                    isOk ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                  }`}>
                    {status}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Live Audit Log Stream */}
        <div className="lg:col-span-2 bg-navy-800 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Live Audit & Screening Activity Log</h3>
            <span className="text-[11px] text-slate-400 font-mono">Immutable Provenance Trail</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-700/80 text-slate-400">
                  <th className="pb-2 font-medium">Timestamp</th>
                  <th className="pb-2 font-medium">Officer / Actor</th>
                  <th className="pb-2 font-medium">Action Event</th>
                  <th className="pb-2 font-medium">Resource Ref</th>
                  <th className="pb-2 font-medium text-right">Outcome</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {metrics?.recent_activity?.map((act) => (
                  <tr key={act.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-2.5 font-mono text-[11px] text-slate-400">{act.timestamp}</td>
                    <td className="py-2.5 font-medium text-sky-300">{act.actor}</td>
                    <td className="py-2.5 font-mono text-[11px]">{act.action}</td>
                    <td className="py-2.5 text-slate-400 font-mono text-[11px]">
                      {act.resource?.startsWith('case:') ? (
                        <button
                          onClick={() => {
                            const caseId = parseInt(act.resource.split(':')[1], 10);
                            if (!isNaN(caseId)) onNavigateToCase(caseId);
                          }}
                          className="text-sky-400 hover:underline cursor-pointer"
                        >
                          {act.resource}
                        </button>
                      ) : (
                        act.resource
                      )}
                    </td>
                    <td className="py-2.5 text-right">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                        {act.outcome}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
