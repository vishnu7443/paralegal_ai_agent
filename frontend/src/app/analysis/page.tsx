"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ArrowLeft, Cpu, ShieldCheck, Search, Info } from "lucide-react";
import AgentStatusBar from "../../components/AgentStatusBar";
import RiskGauge from "../../components/RiskGauge";
import StreamingReport from "../../components/StreamingReport";
import PDFExportButton from "../../components/PDFExportButton";
import RiskTable from "../../components/RiskTable";
import ClauseHeatmap from "../../components/ClauseHeatmap";
import { useSSE } from "../../hooks/useSSE";
import { getAnalysisReport, getJobClauses, searchDocument, API_BASE_URL } from "../../lib/api";
import { Clause } from "../../lib/types";
import confetti from "canvas-confetti";

function DashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const jobId = searchParams.get("jobId");

  const [documentId, setDocumentId] = useState<number | null>(null);
  const [filename, setFilename] = useState<string>("Analyzing Contract...");
  const [clauses, setClauses] = useState<Clause[]>([]);
  const [selectedClauseId, setSelectedClauseId] = useState<number | null>(null);
  
  // Ad-hoc Semantic Search State
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [showSearchModal, setShowSearchModal] = useState(false);

  // Initialize SSE event hook
  const {
    logs,
    reportMarkdown,
    jobStatus,
    isComplete,
    error,
    setReportMarkdown,
    setJobStatus,
    setIsComplete
  } = useSSE(jobId);

  // 1. Initial REST check: see if job was already completed in the DB
  useEffect(() => {
    if (!jobId) return;

    async function checkJobStatus() {
      if (!jobId) return;
      try {
        const data = await getAnalysisReport(jobId);
        setDocumentId(data.document_id);
        if (data.document) {
          setFilename(data.document.filename);
        }

        if (data.status === "COMPLETED") {
          setJobStatus("COMPLETED");
          setIsComplete(true);
          setReportMarkdown(data.report_markdown || "");
          fetchCompletedResults(data.document_id);
        }
      } catch (err) {
        console.warn("Failed to fetch initial report:", err);
      }
    }
    
    checkJobStatus();
  }, [jobId]);

  // 2. Fetch completed results (clauses list) when job transitions to COMPLETED
  useEffect(() => {
    if (isComplete && jobId) {
      triggerConfetti();
      // Load clauses and details
      if (documentId) {
        fetchCompletedResults(documentId);
      } else {
        // Fetch report first to get documentId
        getAnalysisReport(jobId).then(data => {
          setDocumentId(data.document_id);
          fetchCompletedResults(data.document_id);
        });
      }
    }
  }, [isComplete, jobId]);

  const fetchCompletedResults = async (docId: number) => {
    if (!jobId) return;
    try {
      const fetchedClauses = await getJobClauses(jobId);
      setClauses(fetchedClauses);
    } catch (e) {
      console.warn("Failed to load clauses:", e);
    }
  };

  const triggerConfetti = () => {
    confetti({
      particleCount: 80,
      spread: 60,
      origin: { y: 0.6 }
    });
  };

  // 3. Ad-hoc semantic search handler
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!documentId || !searchQuery.trim()) return;

    setSearching(true);
    setSearchResults([]);
    try {
      const results = await searchDocument(documentId, searchQuery, 3);
      setSearchResults(results);
    } catch (err) {
      console.error("Ad-hoc search failed:", err);
    } finally {
      setSearching(false);
    }
  };

  // Get current active risk rating score
  const getOverallRiskScore = () => {
    // If completed, compute it or load it.
    // We will compute average score of clauses, or use baseline 5.0 during loading
    if (!isComplete) return 5.0;
    if (clauses.length === 0) return 1.0;
    
    const topScores = clauses.slice(0, 3).map(c => c.risk_score);
    return parseFloat((topScores.reduce((a, b) => a + b, 0) / topScores.length).toFixed(1));
  };

  const activeRiskScore = getOverallRiskScore();

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-slate-100 to-slate-200 dark:from-[#090b11] dark:via-[#0c0f17] dark:to-[#121622] py-8 px-4 sm:px-6 lg:px-8 text-slate-800 dark:text-slate-200 font-sans">
      <div className="max-w-7xl mx-auto space-y-8 animate-fade-in-up">
        
        {/* Header Session Navigation */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-850 pb-6">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.push("/")}
              className="p-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:hover:bg-slate-850 transition-all active:scale-95"
              aria-label="Back to landing page"
            >
              <ArrowLeft className="w-4.5 h-4.5" />
            </button>
            
            <div>
              <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block dark:text-slate-500">
                Active Audit Session
              </span>
              <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-50 flex items-center gap-2">
                <Cpu className="w-5 h-5 text-sky-500" />
                {filename}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-2 select-none">
            {isComplete && documentId && (
              <button
                onClick={() => setShowSearchModal(true)}
                className="flex items-center gap-1.5 text-xs font-bold bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-sky-500/50 hover:bg-slate-50 dark:hover:bg-slate-850 px-3.5 py-2 rounded-xl transition-all"
              >
                <Search className="w-3.5 h-3.5 text-sky-500" />
                Semantic Clause Search
              </button>
            )}
            
            <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase">
              <span className="bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200/50 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-450 font-mono text-[9px]">
                ID: {jobId ? jobId.slice(0, 18) : "loading"}...
              </span>
            </div>
          </div>
        </div>

        {/* Real-time Agent Reasoning feed */}
        <AgentStatusBar logs={logs} jobStatus={jobStatus} />

        {/* Dashboard Grid Content */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Left Area (8 cols): Streaming report, and once complete, detailed clause list */}
          <div className="lg:col-span-8 space-y-6">
            <StreamingReport
              markdown={reportMarkdown}
              isComplete={isComplete}
              onDownloadPdf={() => window.open(`${API_BASE_URL}/report/${jobId}/pdf`)}
            />

            {/* Display detailed RiskTable and Heatmap view side-by-side once analysis completes */}
            {isComplete && clauses.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6 border-t border-slate-200 dark:border-slate-850">
                <RiskTable
                  clauses={clauses}
                  selectedClauseId={selectedClauseId}
                  onSelectClause={setSelectedClauseId}
                />
                
                <ClauseHeatmap
                  clauses={clauses}
                  selectedClauseId={selectedClauseId}
                  onSelectClause={setSelectedClauseId}
                />
              </div>
            )}
          </div>

          {/* Right Area (4 cols): overall risk dial & PDF export actions */}
          <div className="lg:col-span-4 space-y-6 lg:sticky lg:top-8">
            <RiskGauge score={isComplete ? activeRiskScore : 5.0} />

            {isComplete && jobId && (
              <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-md space-y-4">
                <h4 className="font-bold text-xs uppercase tracking-wider text-slate-400 pl-1 dark:text-slate-500">
                  Export Audit Brief
                </h4>
                <p className="text-xs text-slate-450 dark:text-slate-400 leading-relaxed pl-1">
                  Compile the agent crew's log reasonings, risk assessments, and executive brief report into a premium ReportLab PDF.
                </p>
                <PDFExportButton jobId={jobId} />
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Ad-hoc Semantic Search Modal Overlay */}
      {showSearchModal && (
        <div className="fixed inset-0 bg-slate-950/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-[#0d1017] rounded-3xl border border-slate-200 dark:border-slate-800 max-w-xl w-full p-6 space-y-4 shadow-2xl relative animate-fade-in">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-850 pb-3">
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
                <Search className="w-4 h-4 text-sky-500" />
                Ad-hoc Semantic Clause Search
              </h3>
              <button
                onClick={() => {
                  setShowSearchModal(false);
                  setSearchQuery("");
                  setSearchResults([]);
                }}
                className="text-xs font-bold text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 uppercase px-2 py-1 rounded"
              >
                Close
              </button>
            </div>

            <form onSubmit={handleSearch} className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Ask about indemnification limit, duration, etc."
                className="flex-1 px-4 py-2.5 rounded-xl border border-slate-250 bg-slate-50/50 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 text-xs dark:bg-slate-950 dark:border-slate-800 text-slate-200"
              />
              <button
                type="submit"
                disabled={searching || !searchQuery.trim()}
                className="bg-sky-600 hover:bg-sky-500 text-white font-bold px-4 py-2.5 rounded-xl text-xs transition-all disabled:opacity-40"
              >
                {searching ? "Searching..." : "Search"}
              </button>
            </form>

            <div className="space-y-4 max-h-[300px] overflow-y-auto pr-1">
              {searching && (
                <p className="text-center text-xs text-slate-400 italic py-6 animate-pulse">
                  Querying local FAISS vector index...
                </p>
              )}
              
              {!searching && searchResults.length === 0 && searchQuery && (
                <p className="text-center text-xs text-slate-400 italic py-6">
                  No matching contract segments found.
                </p>
              )}

              {!searching && searchResults.map((res, i) => (
                <div
                  key={i}
                  className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-850 bg-slate-50/30 dark:bg-slate-950/20 space-y-2"
                >
                  <div className="flex items-center justify-between text-[9px] font-bold text-slate-400 uppercase font-mono">
                    <span>Match #{i+1} • Similarity: {res.score.toFixed(4)}</span>
                    <span>Page {res.page_num}</span>
                  </div>
                  <p className="text-xs text-slate-700 dark:text-slate-350 leading-relaxed font-normal">
                    {res.text}
                  </p>
                  <div className="flex items-center gap-1.5 text-[9px] font-bold uppercase select-none">
                    <span className="bg-sky-500/10 text-sky-600 px-1.5 py-0.5 rounded">
                      {res.risk_category}
                    </span>
                    <span className="bg-rose-500/10 text-rose-600 px-1.5 py-0.5 rounded">
                      {res.risk_level} Risk ({res.risk_score})
                    </span>
                    <span className="text-slate-450 dark:text-slate-550 flex items-center gap-0.5">
                      <Info className="w-2.5 h-2.5 text-sky-500" />
                      {res.risk_explanation}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AnalysisPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-[#090b11] text-slate-400 dark:text-slate-650 italic">
        Loading session parameters...
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
