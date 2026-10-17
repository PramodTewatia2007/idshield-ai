import React, { useState } from 'react';
import { Search, Globe, RefreshCw } from 'lucide-react';
import { apiClient } from '../api/client';
import { OSINTFinding } from '../types';

export const OSINTWorkspacePage: React.FC = () => {
  const [target, setTarget] = useState('Alexander Victor Morgan');
  const [queryType, setQueryType] = useState('identity_name');
  const [loading, setLoading] = useState(false);
  const [findings, setFindings] = useState<OSINTFinding[]>([]);
  const [selectedConnectors, setSelectedConnectors] = useState({
    spiderfoot: true,
    theharvester: true,
    maltego: true,
    sanctions_watch: true,
  });

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const activeConnectors = Object.entries(selectedConnectors)
        .filter(([, active]) => active)
        .map(([name]) => name);

      // Search via case 1 for workspace exploration
      const resp = await apiClient.post('/cases/1/osint-search', {
        query_target: target,
        query_type: queryType,
        connectors: activeConnectors
      });
      setFindings(resp.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-wide">OSINT Investigation Workspace</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Lawful open-source cross-referencing against Maltego transforms, SpiderFoot automated footprints, theHarvester recon, and open sanctions watchlists.
        </p>
      </div>

      {/* Query Bar & Source Config */}
      <div className="bg-navy-800 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="Enter name, passport number, domain or organization..."
              required
              className="w-full bg-navy-900 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
            />
          </div>

          <select
            value={queryType}
            onChange={(e) => setQueryType(e.target.value)}
            className="bg-navy-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
          >
            <option value="identity_name">Individual Name</option>
            <option value="passport_number">Document / Passport Number</option>
            <option value="organization">Corporate / Sponsor Name</option>
            <option value="domain">Public Domain / Email</option>
          </select>

          <button
            type="submit"
            disabled={loading}
            className="px-5 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium flex items-center justify-center space-x-1.5 transition shadow-lg shadow-sky-600/20 disabled:opacity-50"
          >
            {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Globe className="w-3.5 h-3.5" />}
            <span>{loading ? 'Querying Sources...' : 'Execute OSINT Query'}</span>
          </button>
        </form>

        {/* Connector Toggle Pills */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/80">
          <span className="text-[11px] text-slate-400 uppercase font-mono mr-2">Configured Connectors:</span>
          {Object.entries(selectedConnectors).map(([key, active]) => (
            <button
              key={key}
              type="button"
              onClick={() => setSelectedConnectors({ ...selectedConnectors, [key]: !active })}
              className={`px-2.5 py-1 rounded text-xs font-mono transition border ${
                active
                  ? 'bg-sky-500/10 text-sky-400 border-sky-500/30'
                  : 'bg-navy-900 text-slate-500 border-slate-800'
              }`}
            >
              {key === 'spiderfoot' && 'SpiderFoot 3.5'}
              {key === 'theharvester' && 'theHarvester 4.2'}
              {key === 'maltego' && 'Maltego Graph'}
              {key === 'sanctions_watch' && 'OpenSanctions Watch'}
            </button>
          ))}
        </div>
      </div>

      {/* Sourced Intelligence Findings Feed */}
      <div className="space-y-3">
        {findings.map((f, idx) => (
          <div key={idx} className="bg-navy-800 border border-slate-800 rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold text-sky-400">{f.connector_name}</span>
                <span className="text-slate-600">•</span>
                <span className="text-xs text-slate-300">{f.source_name}</span>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                f.investigation_relevance === 'adverse' ? 'bg-red-500/10 text-red-400 border border-red-500/30' : 'bg-slate-700 text-slate-300'
              }`}>
                {f.investigation_relevance.toUpperCase()}
              </span>
            </div>
            <p className="text-xs text-slate-200">{f.finding_summary}</p>
            {f.source_url && (
              <div className="text-[11px] font-mono text-slate-400">
                Source Attribution: <a href={f.source_url} target="_blank" rel="noreferrer" className="text-sky-400 hover:underline">{f.source_url}</a>
              </div>
            )}
            <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1 border-t border-slate-800/60">
              <span>Reliability: {f.reliability_assessment.toUpperCase()}</span>
              <span>Verification: {f.verification_status.toUpperCase()}</span>
            </div>
          </div>
        ))}

        {findings.length === 0 && !loading && (
          <div className="bg-navy-800 border border-slate-800 rounded-xl p-12 text-center text-slate-500 text-xs">
            Enter an entity query above to run lawful cross-border OSINT aggregation.
          </div>
        )}
      </div>
    </div>
  );
};
