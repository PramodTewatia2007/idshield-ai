import React, { useState } from 'react';
import { 
  ShieldAlert, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  ZoomIn, 
  Edit3, 
  Search, 
  Database, 
  UserCheck, 
  Save, 
  Download, 
  Cpu 
} from 'lucide-react';
import { CaseRecord } from '../types';
import { apiClient, API_BASE_URL, STORAGE_BASE_URL } from '../api/client';

interface CaseDetailProps {
  caseData: CaseRecord;
  onRefresh: () => void;
  onBack: () => void;
}

export const CaseDetailPage: React.FC<CaseDetailProps> = ({
  caseData,
  onRefresh,
  onBack
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'analysis' | 'osint' | 'database' | 'face' | 'decision'>('analysis');
  const [editingFieldId, setEditingFieldId] = useState<number | null>(null);
  const [editedValue, setEditedValue] = useState<string>('');
  const [decisionNotes, setDecisionNotes] = useState<string>(caseData.review_notes || '');
  const [savingDecision, setSavingDecision] = useState(false);
  const [runningOSINT, setRunningOSINT] = useState(false);
  const [osintTarget, setOsintTarget] = useState('');
  const [runningDB, setRunningDB] = useState(false);
  const [runningFace, setRunningFace] = useState(false);

  const primaryDoc = caseData.documents?.[0];
  const latestRisk = caseData.risk_assessments?.[caseData.risk_assessments.length - 1];

  const handleSaveFieldCorrection = async (fieldId: number) => {
    try {
      await apiClient.put(`/documents/fields/${fieldId}/correct`, {
        corrected_value: editedValue
      });
      setEditingFieldId(null);
      onRefresh();
    } catch (err) {
      console.error('Failed to correct field', err);
    }
  };

  const handleRecordDecision = async (decision: string) => {
    setSavingDecision(true);
    try {
      await apiClient.post(`/cases/${caseData.id}/review`, {
        decision,
        review_notes: decisionNotes
      });
      onRefresh();
    } catch (err) {
      console.error('Failed to submit decision', err);
    } finally {
      setSavingDecision(false);
    }
  };

  const handleRunOSINT = async () => {
    setRunningOSINT(true);
    try {
      await apiClient.post(`/cases/${caseData.id}/osint-search`, {
        query_target: osintTarget || caseData.title,
        query_type: 'identity_name',
        connectors: ['spiderfoot', 'theharvester', 'maltego', 'sanctions_watch']
      });
      onRefresh();
    } catch (err) {
      console.error(err);
    } finally {
      setRunningOSINT(false);
    }
  };

  const handleRunDatabaseCheck = async () => {
    setRunningDB(true);
    try {
      const docNumField = primaryDoc?.extracted_fields?.find(f => f.field_name === 'passport_number' || f.field_name === 'document_number');
      const docNum = docNumField?.extracted_value || 'P84920194';
      await apiClient.post(`/cases/${caseData.id}/database-check`, {
        document_number: docNum,
        issuing_country: 'UTO',
        services: ['INTERPOL_SLTD', 'NATIONAL_VISA_SYS', 'REVOKED_BULLETIN']
      });
      onRefresh();
    } catch (err) {
      console.error(err);
    } finally {
      setRunningDB(false);
    }
  };

  const handleRunFaceVerification = async () => {
    setRunningFace(true);
    try {
      await apiClient.post(`/cases/${caseData.id}/face-verify`, {});
      onRefresh();
    } catch (err) {
      console.error(err);
    } finally {
      setRunningFace(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Case Header Banner */}
      <div className="bg-navy-800 border border-slate-800 rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <button
              onClick={onBack}
              className="text-xs text-sky-400 hover:text-sky-300 font-mono"
            >
              &larr; Back to Cases
            </button>
            <span className="text-slate-600">•</span>
            <span className="font-mono text-xs px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/30">
              {caseData.case_reference}
            </span>
            <span className="font-mono text-xs text-slate-400">
              Status: {caseData.status.toUpperCase()}
            </span>
          </div>
          <h2 className="text-lg font-bold text-white mt-1">{caseData.title}</h2>
          <p className="text-xs text-slate-400">{caseData.description}</p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-2">
          <a
            href={`${API_BASE_URL}/cases/${caseData.id}/report?token=${localStorage.getItem('idshield_token') || ''}`}
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1.5 rounded-lg bg-navy-900 border border-slate-700 hover:bg-slate-800 text-xs text-slate-200 font-medium flex items-center space-x-1.5 transition"
          >
            <Download className="w-3.5 h-3.5 text-sky-400" />
            <span>Official PDF Report</span>
          </a>
        </div>
      </div>

      {/* Sub Tabs */}
      <div className="flex border-b border-slate-800 space-x-1">
        {[
          { id: 'analysis', label: 'Split-Screen Inspection', icon: ZoomIn },
          { id: 'osint', label: `OSINT Intelligence (${caseData.osint_findings?.length || 0})`, icon: Search },
          { id: 'database', label: `Database Checks (${caseData.database_checks?.length || 0})`, icon: Database },
          { id: 'face', label: `Biometrics & Face (${caseData.face_verifications?.length || 0})`, icon: UserCheck },
          { id: 'decision', label: 'Officer Adjudication', icon: ShieldAlert },
        ].map((tab) => {
          const Icon = tab.icon;
          const active = activeSubTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id as any)}
              className={`px-4 py-2.5 text-xs font-medium border-b-2 transition flex items-center space-x-2 ${
                active
                  ? 'border-sky-500 text-sky-400 bg-navy-800/50'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB 1: Split-Screen Document Analysis */}
      {activeSubTab === 'analysis' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Panel: Document Viewer with Overlays */}
          <div className="bg-navy-800 border border-slate-800 rounded-xl p-4 flex flex-col">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800">
              <span className="text-xs font-semibold text-white">Source Image & Evidence Overlay</span>
              <span className="text-[11px] font-mono text-slate-400">
                {primaryDoc?.file_name || 'No document attached'}
              </span>
            </div>

            {primaryDoc ? (
              <div className="relative rounded-lg overflow-hidden border border-slate-700 bg-black flex items-center justify-center min-h-[400px]">
                {/* Image render */}
                <img
                  src={primaryDoc.file_url ? `${STORAGE_BASE_URL}${primaryDoc.file_url}` : `${STORAGE_BASE_URL}/storage/documents/${primaryDoc.file_path.split('\\').pop()?.split('/').pop()}`}
                  alt="Document Specimen"
                  className="max-h-[460px] w-auto object-contain"
                />

                {/* Overlaid bounding boxes for tampering findings */}
                {primaryDoc.tampering_findings?.map((tf, i) => {
                  const coords = tf.region_coordinates;
                  if (!coords || coords.length < 4) return null;
                  const [x, y, w, h] = coords;
                  // Scale coordinates assuming 720x480 standard canvas
                  const left = `${(x / 720) * 100}%`;
                  const top = `${(y / 480) * 100}%`;
                  const width = `${(w / 720) * 100}%`;
                  const height = `${(h / 480) * 100}%`;
                  return (
                    <div
                      key={i}
                      style={{ left, top, width, height }}
                      className="absolute border-2 border-red-500 bg-red-500/20 pointer-events-none animate-pulse"
                      title={tf.explanation}
                    >
                      <span className="absolute -top-5 left-0 px-1 py-0.5 rounded text-[9px] bg-red-600 text-white font-mono uppercase whitespace-nowrap">
                        {tf.finding_type}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="flex items-center justify-center h-64 text-slate-500 text-xs">
                No document record found for this case.
              </div>
            )}

            {/* Document Hash Integrity */}
            {primaryDoc && (
              <div className="mt-4 p-2.5 rounded-lg bg-navy-900 border border-slate-800 flex items-center justify-between text-[11px]">
                <span className="text-slate-400">SHA-256 Checksum:</span>
                <span className="font-mono text-sky-400 truncate max-w-xs">{primaryDoc.file_hash}</span>
              </div>
            )}
          </div>

          {/* Right Panel: OCR Extraction, Rules & Forensics */}
          <div className="space-y-4">
            {/* Explainable Risk Pill */}
            {latestRisk && (
              <div className="bg-navy-800 border border-slate-800 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-white">Aggregated Risk Assessment</span>
                  <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
                    latestRisk.risk_score > 40 ? 'bg-red-500/20 text-red-400 border border-red-500/40' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                  }`}>
                    {latestRisk.category.toUpperCase()} ({latestRisk.risk_score}/100)
                  </span>
                </div>
                <div className="space-y-1.5 mt-3">
                  {latestRisk.contributing_factors?.map((f, i) => (
                    <div key={i} className="text-xs p-2 rounded bg-navy-900 border border-slate-800/80 flex items-start justify-between">
                      <div>
                        <span className="font-semibold text-slate-200">{f.factor}:</span>
                        <p className="text-slate-400 text-[11px] mt-0.5">{f.explanation}</p>
                      </div>
                      <span className="text-[10px] font-mono text-red-400 shrink-0 ml-2 font-bold">{f.impact}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Extracted Fields Table */}
            <div className="bg-navy-800 border border-slate-800 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800">
                <span className="text-xs font-semibold text-white">OCR Extracted Data & Operator Review</span>
                <span className="text-[11px] text-slate-400">ICAO Doc 9303 Parsed</span>
              </div>

              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {primaryDoc?.extracted_fields?.map((f) => (
                  <div key={f.id} className="p-2 rounded bg-navy-900 border border-slate-800 flex items-center justify-between text-xs">
                    <div className="truncate pr-2">
                      <span className="text-slate-400 block text-[10px] font-mono">{f.field_label}</span>
                      {editingFieldId === f.id ? (
                        <div className="flex items-center space-x-1 mt-1">
                          <input
                            type="text"
                            value={editedValue}
                            onChange={(e) => setEditedValue(e.target.value)}
                            className="bg-navy-950 border border-sky-500 rounded px-2 py-0.5 text-xs text-white"
                          />
                          <button
                            onClick={() => handleSaveFieldCorrection(f.id)}
                            className="p-1 rounded bg-sky-600 text-white hover:bg-sky-500"
                          >
                            <Save className="w-3 h-3" />
                          </button>
                        </div>
                      ) : (
                        <span className="font-semibold text-slate-200">{f.extracted_value || '—'}</span>
                      )}
                    </div>
                    <div className="flex items-center space-x-2 shrink-0">
                      <span className="text-[10px] font-mono text-slate-400">
                        {roundConfidence(f.ocr_confidence)}% conf
                      </span>
                      {f.is_corrected && (
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/30">
                          CORRECTED
                        </span>
                      )}
                      <button
                        onClick={() => {
                          setEditingFieldId(f.id);
                          setEditedValue(f.extracted_value || '');
                        }}
                        className="text-slate-500 hover:text-sky-400 transition"
                        title="Manual Correction"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Validation Engine Results */}
            <div className="bg-navy-800 border border-slate-800 rounded-xl p-4">
              <span className="text-xs font-semibold text-white block mb-3 pb-2 border-b border-slate-800">
                Rule-Based Document Validation Checks
              </span>
              <div className="space-y-2">
                {primaryDoc?.validation_results?.map((vr) => {
                  const isPass = vr.status === 'passed';
                  return (
                    <div key={vr.id} className="p-2 rounded bg-navy-900 border border-slate-800 flex items-start space-x-2 text-xs">
                      {isPass ? (
                        <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                      )}
                      <div>
                        <span className="font-semibold text-slate-200">{vr.rule_name}</span>
                        <p className="text-slate-400 text-[11px] mt-0.5">{vr.explanation}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: OSINT Intelligence */}
      {activeSubTab === 'osint' && (
        <div className="space-y-4">
          <div className="bg-navy-800 border border-slate-800 rounded-xl p-5 flex items-center justify-between">
            <div className="w-full max-w-md">
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Target Entity for OSINT Investigation
              </label>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={osintTarget}
                  onChange={(e) => setOsintTarget(e.target.value)}
                  placeholder={caseData.title}
                  className="w-full bg-navy-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-sky-500"
                />
                <button
                  onClick={handleRunOSINT}
                  disabled={runningOSINT}
                  className="px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium whitespace-nowrap transition"
                >
                  {runningOSINT ? 'Querying Connectors...' : 'Run OSINT Scan'}
                </button>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            {caseData.osint_findings?.map((of) => (
              <div key={of.id} className="bg-navy-800 border border-slate-800 rounded-xl p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-sky-400">{of.connector_name}</span>
                    <span className="text-slate-600">•</span>
                    <span className="text-xs text-slate-300">{of.source_name}</span>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                    of.investigation_relevance === 'adverse' ? 'bg-red-500/10 text-red-400 border border-red-500/30' : 'bg-slate-700 text-slate-300'
                  }`}>
                    {of.investigation_relevance.toUpperCase()}
                  </span>
                </div>
                <p className="text-xs text-slate-300">{of.finding_summary}</p>
                {of.source_url && (
                  <div className="text-[11px] font-mono text-slate-500">
                    Source: <a href={of.source_url} target="_blank" rel="noreferrer" className="text-sky-400 hover:underline">{of.source_url}</a>
                  </div>
                )}
              </div>
            ))}
            {caseData.osint_findings?.length === 0 && (
              <div className="text-center py-12 text-slate-500 text-xs bg-navy-800 rounded-xl border border-slate-800">
                No OSINT findings associated with this case yet. Click 'Run OSINT Scan' to gather intelligence.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: Database Verification */}
      {activeSubTab === 'database' && (
        <div className="space-y-4">
          <div className="bg-navy-800 border border-slate-800 rounded-xl p-5 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">Authorized Database Gateways</h3>
              <p className="text-xs text-slate-400">Query INTERPOL SLTD and National Visa Databases</p>
            </div>
            <button
              onClick={handleRunDatabaseCheck}
              disabled={runningDB}
              className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition"
            >
              {runningDB ? 'Querying Authorities...' : 'Execute Database Verification'}
            </button>
          </div>

          <div className="space-y-3">
            {caseData.database_checks?.map((dc) => {
              const isStolen = dc.response_status === 'revoked_stolen';
              return (
                <div key={dc.id} className="bg-navy-800 border border-slate-800 rounded-xl p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">{dc.source_identifier}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                      isStolen ? 'bg-red-500/20 text-red-400 border border-red-500/40' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                    }`}>
                      {dc.response_status.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300">{dc.explanation}</p>
                  <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between">
                    <span>Ref: {dc.result_reference || 'N/A'}</span>
                    <span>{dc.is_mock ? 'Official Test Gateway (Mock Adapter)' : 'Live Production Gateway'}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 4: Facial Biometric Verification */}
      {activeSubTab === 'face' && (
        <div className="space-y-4">
          <div className="bg-navy-800 border border-slate-800 rounded-xl p-5 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">Authorized 1:1 Facial Biometric Comparison</h3>
              <p className="text-xs text-slate-400">Compares document extracted portrait with live capture presentation under supervisory authorization</p>
            </div>
            <button
              onClick={handleRunFaceVerification}
              disabled={runningFace}
              className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition"
            >
              {runningFace ? 'Extracting Biometrics...' : 'Run Facial Comparison'}
            </button>
          </div>

          <div className="space-y-3">
            {caseData.face_verifications?.map((fv) => (
              <div key={fv.id} className="bg-navy-800 border border-slate-800 rounded-xl p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white font-mono">{fv.verification_method}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                    fv.match_status === 'match' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-red-500/20 text-red-400 border border-red-500/40'
                  }`}>
                    {fv.match_status.toUpperCase()}
                  </span>
                </div>
                <p className="text-xs text-slate-300">{fv.analyst_notes}</p>
                <div className="text-[11px] font-mono text-slate-400">
                  Model: {fv.model_version} • Comparison Score: {roundConfidence(fv.comparison_score)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 5: Officer Adjudication */}
      {activeSubTab === 'decision' && (
        <div className="bg-navy-800 border border-slate-800 rounded-xl p-6 max-w-2xl mx-auto space-y-4">
          <h3 className="text-sm font-bold text-white">Officer Adjudication & Concluding Decision</h3>
          <p className="text-xs text-slate-400">
            Automated findings are decision-support only. Enter reasoned justification for immigration entry, referral or denial.
          </p>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Officer Findings & Justification
            </label>
            <textarea
              value={decisionNotes}
              onChange={(e) => setDecisionNotes(e.target.value)}
              placeholder="Record operational observations, passenger statement, physical security checks performed..."
              rows={4}
              className="w-full bg-navy-900 border border-slate-700 rounded-lg p-3 text-xs text-white focus:outline-none focus:border-sky-500"
            />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
            <button
              onClick={() => handleRecordDecision('APPROVED')}
              disabled={savingDecision}
              className="py-2.5 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition flex items-center justify-center space-x-1"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Approve Entry</span>
            </button>
            <button
              onClick={() => handleRecordDecision('ESCALATED')}
              disabled={savingDecision}
              className="py-2.5 px-3 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-medium transition flex items-center justify-center space-x-1"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Escalate / Review</span>
            </button>
            <button
              onClick={() => handleRecordDecision('HOLD')}
              disabled={savingDecision}
              className="py-2.5 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition flex items-center justify-center space-x-1"
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>Hold for OSINT</span>
            </button>
            <button
              onClick={() => handleRecordDecision('REJECTED')}
              disabled={savingDecision}
              className="py-2.5 px-3 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-medium transition flex items-center justify-center space-x-1"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>Deny Entry</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

function roundConfidence(val: number) {
  return Math.round(val * 100);
}
