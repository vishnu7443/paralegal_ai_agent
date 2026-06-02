"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Gavel, Clock, FileText, AlertTriangle, ArrowRight, ShieldCheck } from "lucide-react";
import UploadZone from "../components/UploadZone";
import ComparePanel from "../components/ComparePanel";
import { listJobs, analyseDocument } from "../lib/api";

export default function LandingPage() {
  const router = useRouter();
  const [recentJobs, setRecentJobs] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  // Fetch job run history
  const fetchHistory = async () => {
    try {
      const jobs = await listJobs();
      setRecentJobs(jobs.slice(0, 5)); // show top 5 recent jobs
    } catch (e) {
      console.warn("Failed to load audit history:", e);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleUploadSuccess = async (docId: number, filename: string) => {
    // Once document is uploaded successfully, dispatch the analysis job
    try {
      console.log(`[Landing] Document uploaded successfully (ID: ${docId}). Dispatching analysis...`);
      const res = await analyseDocument(docId);
      // Route immediately to the analysis page for this job
      router.push(`/analysis?jobId=${res.job_id}`);
    } catch (err: any) {
      console.error("Failed to start analysis:", err);
    }
  };

  const getRiskColor = (score: number | null) => {
    if (score === null) return "text-slate-400 dark:text-slate-600";
    if (score < 4.0) return "text-emerald-500";
    if (score < 7.0) return "text-amber-500";
    if (score < 9.0) return "text-rose-500";
    return "text-purple-500";
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-slate-100 to-slate-200 dark:from-[#090b11] dark:via-[#0c0f17] dark:to-[#121622] py-12 px-4 sm:px-6 lg:px-8 text-slate-800 dark:text-slate-200 font-sans">
      <div className="max-w-4xl mx-auto space-y-12">
        
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center gap-2 select-none">
            <div className="p-3 bg-sky-500/10 text-sky-600 rounded-2xl border border-sky-500/25">
              <Gavel className="w-8 h-8" />
            </div>
          </div>
          <div className="space-y-2">
            <h1 className="text-4xl font-black tracking-tight bg-gradient-to-r from-sky-600 to-sky-400 bg-clip-text text-transparent dark:from-sky-400 dark:to-sky-200 uppercase">
              Paralegal Agentic Auditor
            </h1>
            <p className="text-sm font-semibold tracking-wider text-slate-400 dark:text-slate-500 uppercase">
              Deterministic RAG Multi-Agent Contract Auditor for Small Businesses
            </p>
          </div>
        </div>

        {/* Upload Zone */}
        <div className="space-y-4">
          <h2 className="text-lg font-bold tracking-tight uppercase pl-1 text-slate-400 dark:text-slate-500 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-sky-500" />
            Audit a New Contract
          </h2>
          <UploadZone onUploadSuccess={handleUploadSuccess} />
        </div>

        {/* Historical Runs */}
        <div className="space-y-4">
          <h2 className="text-lg font-bold tracking-tight uppercase pl-1 text-slate-400 dark:text-slate-500 flex items-center gap-2">
            <Clock className="w-5 h-5 text-sky-500" />
            Recent Audits &amp; History
          </h2>
          
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-md overflow-hidden shadow-md divide-y divide-slate-200 dark:divide-slate-800">
            {loadingHistory ? (
              <div className="p-8 text-center text-slate-400 dark:text-slate-650 italic">
                Loading contract history...
              </div>
            ) : recentJobs.length === 0 ? (
              <div className="p-8 text-center text-slate-400 dark:text-slate-650 italic">
                No recent audits found. Upload a PDF to begin.
              </div>
            ) : (
              recentJobs.map((job) => (
                <div
                  key={job.id}
                  onClick={() => router.push(`/analysis?jobId=${job.id}`)}
                  className="p-4 flex items-center justify-between gap-4 cursor-pointer hover:bg-slate-100/50 dark:hover:bg-slate-900/15 transition-all select-none"
                >
                  <div className="flex items-center gap-3 max-w-[70%]">
                    <FileText className="w-5 h-5 text-slate-400 flex-shrink-0" />
                    <div>
                      <h4 className="text-xs font-bold text-slate-800 dark:text-slate-100 truncate">
                        {job.document?.filename || "Sample Contract"}
                      </h4>
                      <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">
                        Audited on: {new Date(job.created_at).toLocaleDateString()} at {new Date(job.created_at).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <span className="text-[9px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest block">
                        Risk Rating
                      </span>
                      <span className={`text-sm font-black font-mono ${getRiskColor(job.risk_score)}`}>
                        {job.risk_score !== null ? `${job.risk_score.toFixed(1)}/10` : "PENDING..."}
                      </span>
                    </div>
                    <ArrowRight className="w-4 h-4 text-slate-350 dark:text-slate-600" />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Compare Panel */}
        <ComparePanel />

      </div>
    </div>
  );
}
