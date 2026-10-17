import React, { useState } from 'react';
import { 
  UploadCloud, 
  CheckCircle, 
  AlertTriangle, 
  Layers, 
  Sparkles
} from 'lucide-react';
import { apiClient } from '../api/client';
import { CaseRecord, DocumentRecord } from '../types';

interface DocumentScreeningProps {
  cases: CaseRecord[];
  onDocumentUploaded: (caseId: number) => void;
}

export const DocumentScreeningPage: React.FC<DocumentScreeningProps> = ({
  cases,
  onDocumentUploaded
}) => {
  const [selectedCaseId, setSelectedCaseId] = useState<number>(cases[0]?.id || 1);
  const [isCreatingNewCase, setIsCreatingNewCase] = useState(false);
  const [newCaseTitle, setNewCaseTitle] = useState('');
  const [docTypeHint, setDocTypeHint] = useState('passport');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<DocumentRecord | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    setError(null);
    setUploadSuccess(null);

    try {
      let targetCaseId = selectedCaseId;

      // Create new case on the fly if needed
      if (isCreatingNewCase) {
        const caseResp = await apiClient.post('/cases', {
          title: newCaseTitle || `Screening - ${selectedFile.name}`,
          description: 'Ad-hoc identity document upload from primary border terminal.'
        });
        targetCaseId = caseResp.data.id;
      }

      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('case_id', targetCaseId.toString());
      formData.append('doc_type_hint', docTypeHint);

      const resp = await apiClient.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setUploadSuccess(resp.data);
      onDocumentUploaded(targetCaseId);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process document upload.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-wide">Document Ingestion & AI Pipeline</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Submit official travel credentials (Passport, Visa, National ID). Automated OCR, ICAO validation, and tamper forensics run automatically.
        </p>
      </div>

      {/* Main Upload Box */}
      <div className="bg-navy-800 border border-slate-800 rounded-xl p-6 shadow-xl">
        <form onSubmit={handleUpload} className="space-y-6">
          {/* Case Association Selector */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Target Case File
              </label>
              <div className="flex space-x-2">
                {!isCreatingNewCase ? (
                  <select
                    value={selectedCaseId}
                    onChange={(e) => setSelectedCaseId(Number(e.target.value))}
                    className="w-full bg-navy-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                  >
                    {cases.map((c) => (
                      <option key={c.id} value={c.id}>
                        [{c.case_reference}] {c.title}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    value={newCaseTitle}
                    onChange={(e) => setNewCaseTitle(e.target.value)}
                    placeholder="Enter new case title / passenger name"
                    required
                    className="w-full bg-navy-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                  />
                )}
                <button
                  type="button"
                  onClick={() => setIsCreatingNewCase(!isCreatingNewCase)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-sky-400 text-xs font-medium whitespace-nowrap transition"
                >
                  {isCreatingNewCase ? 'Pick Existing' : '+ New Case'}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Document Classification Category
              </label>
              <select
                value={docTypeHint}
                onChange={(e) => setDocTypeHint(e.target.value)}
                className="w-full bg-navy-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
              >
                <option value="passport">Passport (ICAO TD3 / e-Passport)</option>
                <option value="visa">Entry / Transit Visa (Schengen/National)</option>
                <option value="national_id">National Identity Card (TD1 / TD2)</option>
                <option value="driving_license">Driving License / Permit</option>
                <option value="residence_permit">Biometric Residence Permit</option>
              </select>
            </div>
          </div>

          {/* Drag & Drop File Zone */}
          <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center bg-navy-900/50 hover:bg-navy-900/80 transition relative">
            <input
              type="file"
              accept="image/*,application/pdf"
              onChange={handleFileChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <div className="flex flex-col items-center justify-center space-y-2">
              <div className="p-3 bg-sky-500/10 rounded-full text-sky-400 border border-sky-500/20">
                <UploadCloud className="w-8 h-8" />
              </div>
              <p className="text-sm font-medium text-slate-200">
                {selectedFile ? selectedFile.name : 'Drag & drop identity credential or click to browse'}
              </p>
              <p className="text-xs text-slate-500 font-mono">
                Accepted: JPG, PNG, WEBP, PDF (Up to 20MB) • SHA-256 Verified
              </p>
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center space-x-2 text-xs text-red-400">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={!selectedFile || uploading}
            className="w-full py-3 px-4 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium text-sm transition shadow-lg shadow-sky-600/20 flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {uploading ? (
              <>
                <Sparkles className="w-4 h-4 animate-spin text-white" />
                <span>Processing OCR, Checksums & Forensic Analysis...</span>
              </>
            ) : (
              <>
                <Layers className="w-4 h-4" />
                <span>Ingest & Run Automated Security Screening</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Immediate Pipeline Outcome Card */}
      {uploadSuccess && (
        <div className="bg-navy-800 border border-emerald-500/30 rounded-xl p-6 space-y-4 animate-in fade-in">
          <div className="flex items-center justify-between border-b border-slate-700/60 pb-3">
            <div className="flex items-center space-x-2 text-emerald-400">
              <CheckCircle className="w-5 h-5" />
              <h3 className="text-sm font-bold">Document Successfully Screened</h3>
            </div>
            <span className="font-mono text-xs text-slate-400">
              SHA-256: {uploadSuccess.file_hash.substring(0, 16)}...
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="bg-navy-900 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400 block mb-1">OCR Extracted Fields</span>
              <span className="text-base font-bold text-white">
                {uploadSuccess.extracted_fields?.length || 0} Fields
              </span>
            </div>
            <div className="bg-navy-900 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400 block mb-1">Validation Rules Checked</span>
              <span className="text-base font-bold text-sky-400">
                {uploadSuccess.validation_results?.length || 0} Rules
              </span>
            </div>
            <div className="bg-navy-900 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400 block mb-1">Forensic Anomalies Found</span>
              <span className={`text-base font-bold ${
                (uploadSuccess.tampering_findings?.length || 0) > 0 ? 'text-red-400' : 'text-emerald-400'
              }`}>
                {uploadSuccess.tampering_findings?.length || 0} Findings
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
