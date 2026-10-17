import React, { useState } from 'react';
import { 
  Search, 
  Filter, 
  Plus, 
  Eye, 
  Download 
} from 'lucide-react';
import { CaseRecord, CaseStatus } from '../types';
import { apiClient, API_BASE_URL } from '../api/client';

interface CaseManagementProps {
  cases: CaseRecord[];
  onSelectCase: (caseId: number) => void;
  onRefreshCases: () => void;
}

export const CaseManagementPage: React.FC<CaseManagementProps> = ({
  cases,
  onSelectCase,
  onRefreshCases
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showNewModal, setShowNewModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [creating, setCreating] = useState(false);

  const filteredCases = cases.filter((c) => {
    const matchesSearch = 
      c.case_reference.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.title.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || c.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await apiClient.post('/cases', {
        title: newTitle,
        description: newDesc
      });
      setShowNewModal(false);
      setNewTitle('');
      setNewDesc('');
      onRefreshCases();
    } catch (err) {
      console.error(err);
    } finally {
      setCreating(false);
    }
  };

  const getStatusBadge = (status: CaseStatus) => {
    switch (status) {
      case 'new':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-sky-500/10 text-sky-400 border border-sky-500/30">NEW</span>;
      case 'manual_review_required':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-red-500/10 text-red-400 border border-red-500/30">REVIEW REQ</span>;
      case 'under_investigation':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/10 text-amber-400 border border-amber-500/30">INVESTIGATION</span>;
      case 'closed':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-700/60 text-slate-300 border border-slate-600">CLOSED</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">Screening Case Registry</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Central repository of cross-border passenger investigations, evidentiary documents & audit trails
          </p>
        </div>
        <button
          onClick={() => setShowNewModal(true)}
          className="px-3.5 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium flex items-center space-x-1.5 transition shadow-lg shadow-sky-600/20"
        >
          <Plus className="w-4 h-4" />
          <span>Open Investigation Case</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-navy-800 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by Case Ref or Title..."
            className="w-full bg-navy-900 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-sky-500"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-navy-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-sky-500"
          >
            <option value="all">All Case Statuses</option>
            <option value="new">New</option>
            <option value="manual_review_required">Manual Review Required</option>
            <option value="under_investigation">Under Investigation</option>
            <option value="closed">Closed / Adjudicated</option>
          </select>
        </div>
      </div>

      {/* Cases Table */}
      <div className="bg-navy-800 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-700/80 bg-navy-900/60 text-slate-400 uppercase tracking-wider font-mono">
                <th className="py-3 px-4 font-medium">Case Ref</th>
                <th className="py-3 px-4 font-medium">Subject / Title</th>
                <th className="py-3 px-4 font-medium">Status</th>
                <th className="py-3 px-4 font-medium">Risk Score</th>
                <th className="py-3 px-4 font-medium">Docs</th>
                <th className="py-3 px-4 font-medium">Created</th>
                <th className="py-3 px-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-slate-300">
              {filteredCases.map((c) => {
                const latestRisk = c.risk_assessments?.[c.risk_assessments.length - 1];
                const score = latestRisk?.risk_score ?? 0;
                return (
                  <tr key={c.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-mono font-semibold text-sky-400">
                      {c.case_reference}
                    </td>
                    <td className="py-3 px-4 font-medium max-w-xs truncate text-white">
                      {c.title}
                    </td>
                    <td className="py-3 px-4">
                      {getStatusBadge(c.status)}
                    </td>
                    <td className="py-3 px-4 font-mono font-bold">
                      <span className={`px-2 py-0.5 rounded text-[11px] ${
                        score > 40 ? 'bg-red-500/10 text-red-400 border border-red-500/30' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      }`}>
                        {score} / 100
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-400">
                      {c.documents?.length || 0}
                    </td>
                    <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                      {c.created_at ? String(c.created_at).substring(0, 10) : ''}
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <button
                        onClick={() => onSelectCase(c.id)}
                        className="px-2.5 py-1 rounded bg-sky-600/20 hover:bg-sky-600/40 text-sky-300 text-xs font-medium border border-sky-500/30 transition inline-flex items-center space-x-1"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </button>
                      <a
                        href={`${API_BASE_URL}/cases/${c.id}/report`}
                        target="_blank"
                        rel="noreferrer"
                        className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-white transition inline-block align-middle"
                        title="Download PDF Report"
                      >
                        <Download className="w-4 h-4" />
                      </a>
                    </td>
                  </tr>
                );
              })}
              {filteredCases.length === 0 && (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-slate-500">
                    No matching cases found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create New Case Modal */}
      {showNewModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-navy-800 border border-slate-700 rounded-xl p-6 w-full max-w-md shadow-2xl">
            <h3 className="text-base font-bold text-white mb-4">Initialize New Investigation Case</h3>
            <form onSubmit={handleCreateCase} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Case Title / Target Subject</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Passenger Inspection - Viktor Kaslov"
                  required
                  className="w-full bg-navy-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Initial Brief / Circumstances</label>
                <textarea
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Enter context, border transit checkpoint, officer notes..."
                  rows={3}
                  className="w-full bg-navy-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition"
                >
                  {creating ? 'Creating...' : 'Create Case File'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
