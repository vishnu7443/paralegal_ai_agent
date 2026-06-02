"use client";

import React, { useState, useEffect } from "react";
import { Layers, CheckSquare, Square, FileText, ChevronRight, BarChart } from "lucide-react";
import { listJobs, compareDocuments } from "../lib/api";
import { ComparisonItem } from "../lib/types";

export default function ComparePanel() {
  const [jobsList, setJobsList] = useState<any[]>([]);
  const [selectedJobIds, setSelectedJobIds] = useState<string[]>([]);
  const [comparisonResults, setComparisonResults] = useState<ComparisonItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all completed jobs on panel load
  useEffect(() => {
    async function loadJobs() {
      try {
        const jobs = await listJobs();
        // Filter to keep only completed jobs
        const completedJobs = jobs.filter((j: any) => j.status === "COMPLETED");
        setJobsList(completedJobs);
      } catch (err) {
        console.warn("Failed to load completed jobs list:", err);
      }
    }
    loadJobs();
  }, []);

  const handleToggleSelect = (jobId: string) => {
    setSelectedJobIds((prev) => {
      if (prev.includes(jobId)) {
        return prev.filter((id) => id !== jobId);
      } else {
        return [...prev, jobId];
      }
    });
  };

  const handleCompare = async () => {
    if (selectedJobIds.length < 2) {
      setError("Please select at least 2 contracts to compare.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const results = await compareDocuments(selectedJobIds);
      setComparisonResults(results);
    } catch (err: any) {
      setError(err.message || "Failed to compare selected contracts.");
    } finally {
      setLoading(false);
    }
  };

  const getRiskScoreColor = (score: number) => {
    if (score < 4.0) return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
    if (score < 7.0) return "text-amber-500 bg-amber-500/10 border-amber-500/20";
    if (score < 9.0) return "text-rose-500 bg-rose-500/10 border-rose-500/20";
    return "text-purple-500 bg-purple-500/10 border-purple-500/20";
  };

  return (
    <div className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-md shadow-lg space-y-6">
      <div className="flex items-center gap-2">
        <Layers className="w-5 h-5 text-sky-500" />
        <div>
          <h3 className="font-bold text-base text-slate-900 dark:text-slate-50">
            Multi-Document Risk Comparison
          </h3>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">
            Select and compare legal documents side-by-side.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
        {/* Left Side: Selectable completed jobs list (5 cols) */}
        <div className="md:col-span-5 space-y-4">
          <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest block pl-1">
            Available Contracts
          </span>
          <div className="max-h-[220px] overflow-y-auto border border-slate-200 dark:border-slate-800 rounded-xl divide-y divide-slate-200 dark:divide-slate-800 bg-slate-50/20 dark:bg-slate-950/20">
            {jobsList.length === 0 ? (
              <p className="p-4 text-xs text-center text-slate-400 dark:text-slate-650 italic">
                No completed contract audits found. Conduct an audit first.
              </p>
            ) : (
              jobsList.map((job) => {
                const isSelected = selectedJobIds.includes(job.id);
                return (
                  <div
                    key={job.id}
                    onClick={() => handleToggleSelect(job.id)}
                    className="p-3 flex items-center justify-between gap-3 cursor-pointer hover:bg-slate-100/50 dark:hover:bg-slate-900/15 transition-all select-none"
                  >
                    <div className="flex items-center gap-2 max-w-[80%]">
                      {isSelected ? (
                        <CheckSquare className="w-4 h-4 text-sky-500 flex-shrink-0" />
                      ) : (
                        <Square className="w-4 h-4 text-slate-350 dark:text-slate-700 flex-shrink-0" />
                      )}
                      <FileText className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                      <span className="text-xs font-semibold truncate text-slate-700 dark:text-slate-300">
                        {job.document?.filename || "Unnamed document"}
                      </span>
                    </div>
                    <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 font-mono">
                      Score: {job.risk_score?.toFixed(1) || "N/A"}
                    </span>
                  </div>
                );
              })
            )}
          </div>

          <button
            onClick={handleCompare}
            disabled={selectedJobIds.length < 2 || loading}
            className="w-full bg-slate-850 hover:bg-slate-950 text-white font-bold py-2.5 px-4 rounded-xl text-xs flex items-center justify-center gap-1.5 transition-all shadow-md disabled:opacity-40 disabled:pointer-events-none dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200"
          >
            {loading ? (
              <>
                <div className="w-3 h-3 border-2 border-white dark:border-slate-900 border-t-transparent rounded-full animate-spin" />
                Comparing...
              </>
            ) : (
              <>
                <ChevronRight className="w-4 h-4" />
                Compare Selected ({selectedJobIds.length})
              </>
            )}
          </button>
          
          {error && (
            <p className="text-[10px] font-bold text-red-500 uppercase tracking-wide text-center">
              {error}
            </p>
          )}
        </div>

        {/* Right Side: Comparison results layout (7 cols) */}
        <div className="md:col-span-7 space-y-4">
          <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest block pl-1">
            Metrics Breakdown
          </span>
          {comparisonResults.length === 0 ? (
            <div className="h-[275px] border border-slate-200 dark:border-slate-800 rounded-xl flex flex-col items-center justify-center gap-2 text-slate-400 dark:text-slate-650 bg-slate-50/10 dark:bg-slate-950/10 select-none">
              <BarChart className="w-8 h-8 text-slate-300 dark:text-slate-750" />
              <p className="text-xs italic">Select 2+ documents and click compare.</p>
            </div>
          ) : (
            <div className="space-y-4 max-h-[275px] overflow-y-auto pr-1">
              {comparisonResults.map((item) => (
                <div
                  key={item.job_id}
                  className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/60 shadow-sm flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 max-w-[70%]">
                    <h4 className="text-xs font-bold text-slate-800 dark:text-slate-100 truncate">
                      {item.filename}
                    </h4>
                    <div className="flex flex-wrap items-center gap-1.5 select-none">
                      <span className="text-[9px] font-extrabold uppercase bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded border border-slate-200/50 dark:bg-slate-950 dark:border-slate-850 dark:text-slate-450">
                        {item.clause_count} Risks Flagged
                      </span>
                      <span className="text-[9px] font-bold bg-purple-100 text-purple-750 dark:bg-purple-900/20 dark:text-purple-400 px-1.5 py-0.5 rounded">
                        {item.severity_breakdown.critical} Critical
                      </span>
                      <span className="text-[9px] font-bold bg-rose-100 text-rose-750 dark:bg-rose-900/20 dark:text-rose-400 px-1.5 py-0.5 rounded">
                        {item.severity_breakdown.high} High
                      </span>
                    </div>
                  </div>

                  {/* Score circle badge */}
                  <div className="flex items-center gap-3 justify-end">
                    <div className="text-right">
                      <span className="text-[8px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest block">
                        Threat Score
                      </span>
                      <span className="text-xs font-semibold text-slate-550 dark:text-slate-400">
                        out of 10
                      </span>
                    </div>
                    <div className={`w-12 h-12 rounded-full border flex items-center justify-center font-black text-sm ${getRiskScoreColor(item.risk_score)}`}>
                      {item.risk_score.toFixed(1)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
