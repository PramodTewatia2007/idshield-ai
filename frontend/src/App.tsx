import React, { useEffect, useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { DocumentScreeningPage } from './pages/DocumentScreeningPage';
import { CaseManagementPage } from './pages/CaseManagementPage';
import { CaseDetailPage } from './pages/CaseDetailPage';
import { OSINTWorkspacePage } from './pages/OSINTWorkspacePage';
import { AdminAuditPage } from './pages/AdminAuditPage';
import { apiClient, API_BASE_URL } from './api/client';
import { CaseRecord, User } from './types';

export default function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(() => {
    try {
      const storedUser = localStorage.getItem('idshield_user');
      const storedToken = localStorage.getItem('idshield_token');
      if (storedUser && storedToken) {
        return JSON.parse(storedUser);
      }
    } catch {
      localStorage.removeItem('idshield_user');
    }
    return null;
  });
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [cases, setCases] = useState<CaseRecord[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null);

  const fetchCases = async () => {
    try {
      const resp = await apiClient.get('/cases');
      setCases(resp.data);
    } catch (err) {
      console.error('Failed to fetch cases', err);
    }
  };

  useEffect(() => {
    if (!currentUser) return;
    let isMounted = true;
    apiClient.get('/cases').then((resp) => {
      if (isMounted) setCases(resp.data);
    }).catch((err) => {
      console.error('Failed to fetch cases', err);
    });
    return () => {
      isMounted = false;
    };
  }, [currentUser]);

  const handleLogout = () => {
    localStorage.removeItem('idshield_token');
    localStorage.removeItem('idshield_user');
    setCurrentUser(null);
  };

  if (!currentUser) {
    return <LoginPage onSuccess={(user) => setCurrentUser(user)} />;
  }

  const selectedCaseData = cases.find((c) => c.id === selectedCaseId);

  return (
    <div className="flex bg-navy-900 min-h-screen text-slate-100">
      {/* Fixed Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
          if (tab !== 'cases') setSelectedCaseId(null);
        }}
        currentUser={currentUser}
        onLogout={handleLogout}
      />

      {/* Main Content Area */}
      <main className="flex-1 ml-64 p-8 overflow-y-auto min-h-screen">
        {selectedCaseId && selectedCaseData ? (
          <CaseDetailPage
            caseData={selectedCaseData}
            onRefresh={fetchCases}
            onBack={() => setSelectedCaseId(null)}
          />
        ) : (
          <>
            {activeTab === 'dashboard' && (
              <DashboardPage onNavigateToCase={(id) => setSelectedCaseId(id)} />
            )}
            {activeTab === 'screening' && (
              <DocumentScreeningPage
                cases={cases}
                onDocumentUploaded={(caseId) => {
                  fetchCases();
                  setSelectedCaseId(caseId);
                }}
              />
            )}
            {activeTab === 'cases' && (
              <CaseManagementPage
                cases={cases}
                onSelectCase={(id) => setSelectedCaseId(id)}
                onRefreshCases={fetchCases}
              />
            )}
            {activeTab === 'review_queue' && (
              <CaseManagementPage
                cases={cases.filter((c) => c.status === 'manual_review_required' || c.status === 'new')}
                onSelectCase={(id) => setSelectedCaseId(id)}
                onRefreshCases={fetchCases}
              />
            )}
            {activeTab === 'osint' && <OSINTWorkspacePage />}
            {activeTab === 'face_verify' && (
              <div className="space-y-4 max-w-2xl">
                <h2 className="text-xl font-bold text-white">Biometric Verification Portal</h2>
                <p className="text-xs text-slate-400">
                  Select any active case from the Case Management registry to execute 1:1 facial biometric comparisons.
                </p>
                <div className="bg-navy-800 border border-slate-800 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-white mb-2">Active Inspection Cases:</h3>
                  <div className="space-y-2">
                    {cases.map((c) => (
                      <button
                        key={c.id}
                        onClick={() => setSelectedCaseId(c.id)}
                        className="w-full text-left p-3 rounded-lg bg-navy-900 border border-slate-800 hover:border-sky-500 text-xs flex justify-between items-center transition"
                      >
                        <div>
                          <span className="font-bold text-sky-400 font-mono">[{c.case_reference}]</span>
                          <span className="text-slate-200 ml-2">{c.title}</span>
                        </div>
                        <span className="text-slate-400 font-mono">Verify Portrait &rarr;</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
            {activeTab === 'reports' && (
              <div className="space-y-4">
                <h2 className="text-xl font-bold text-white">Screening & Forensic Reports Directory</h2>
                <p className="text-xs text-slate-400">
                  Direct official PDF export repository for completed border examinations.
                </p>
                <div className="bg-navy-800 border border-slate-800 rounded-xl p-5">
                  <div className="space-y-3">
                    {cases.map((c) => (
                      <div
                        key={c.id}
                        className="flex items-center justify-between p-3 rounded-lg bg-navy-900 border border-slate-800"
                      >
                        <div>
                          <span className="font-mono text-sky-400 font-bold text-xs">{c.case_reference}</span>
                          <span className="text-white text-xs font-semibold ml-2">{c.title}</span>
                          <span className="text-slate-500 text-xs ml-2">({c.status})</span>
                        </div>
                        <a
                          href={`${API_BASE_URL}/cases/${c.id}/report`}
                          target="_blank"
                          rel="noreferrer"
                          className="px-3 py-1.5 rounded-lg bg-sky-600/20 hover:bg-sky-600/40 text-sky-300 border border-sky-500/30 text-xs font-medium font-mono"
                        >
                          Download Official PDF
                        </a>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
            {activeTab === 'audit' && <AdminAuditPage />}
          </>
        )}
      </main>
    </div>
  );
};
