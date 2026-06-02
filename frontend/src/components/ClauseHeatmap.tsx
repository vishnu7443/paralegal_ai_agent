"use client";

import React, { useEffect, useRef } from "react";
import { FileText, Eye } from "lucide-react";
import { Clause } from "../lib/types";

interface ClauseHeatmapProps {
  clauses: Clause[];
  selectedClauseId: number | null;
  onSelectClause: (clauseId: number) => void;
}

export default function ClauseHeatmap({ clauses, selectedClauseId, onSelectClause }: ClauseHeatmapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const clauseRefs = useRef<Record<number, HTMLDivElement | null>>({});

  // Sort clauses chronologically by document flow (Page first, then block idx)
  const sortedClauses = [...clauses].sort((a, b) => {
    if (a.page_num !== b.page_num) {
      return a.page_num - b.page_num;
    }
    return a.block_num - b.block_num;
  });

  // Smooth scroll selected clause into view
  useEffect(() => {
    if (selectedClauseId !== null && clauseRefs.current[selectedClauseId]) {
      clauseRefs.current[selectedClauseId]?.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }
  }, [selectedClauseId]);

  const getHeatmapColor = (level: string, isSelected: boolean) => {
    if (isSelected) {
      switch (level) {
        case "Critical": return "bg-purple-500/20 border-purple-500 shadow-md ring-2 ring-purple-500/20";
        case "High": return "bg-rose-500/20 border-rose-500 shadow-md ring-2 ring-rose-500/20";
        case "Medium": return "bg-amber-500/20 border-amber-500 shadow-md ring-2 ring-amber-500/20";
        default: return "bg-emerald-500/20 border-emerald-500 shadow-md ring-2 ring-emerald-500/20";
      }
    }
    
    switch (level) {
      case "Critical":
        return "bg-purple-500/5 hover:bg-purple-500/10 border-purple-500/30 hover:border-purple-500/50";
      case "High":
        return "bg-rose-500/5 hover:bg-rose-500/10 border-rose-500/30 hover:border-rose-500/50";
      case "Medium":
        return "bg-amber-500/5 hover:bg-amber-500/10 border-amber-500/30 hover:border-amber-500/50";
      default:
        return "bg-emerald-500/20 dark:bg-emerald-500/5 hover:bg-emerald-500/10 border-emerald-500/20 hover:border-emerald-500/30";
    }
  };

  const getLabelColor = (level: string) => {
    switch (level) {
      case "Critical": return "text-purple-600 dark:text-purple-400";
      case "High": return "text-rose-600 dark:text-rose-400";
      case "Medium": return "text-amber-600 dark:text-amber-400";
      default: return "text-emerald-600 dark:text-emerald-400";
    }
  };

  // Group clauses by page
  const pages: Record<number, Clause[]> = {};
  sortedClauses.forEach((c) => {
    if (!pages[c.page_num]) {
      pages[c.page_num] = [];
    }
    pages[c.page_num].push(c);
  });

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-md overflow-hidden shadow-md flex flex-col h-full">
      {/* Header Panel */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-900/25">
        <div className="flex items-center gap-2">
          <Eye className="w-5 h-5 text-sky-500" />
          <h3 className="font-bold text-sm text-slate-800 dark:text-slate-100">
            Document Heatmap &amp; Reading Flow
          </h3>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase">
          <FileText className="w-3.5 h-3.5" />
          <span>NDA Audit Flow</span>
        </div>
      </div>

      {/* Pages Container */}
      <div ref={containerRef} className="p-6 overflow-y-auto max-h-[480px] space-y-8 bg-slate-50/20 dark:bg-slate-950/20">
        {Object.keys(pages).length === 0 ? (
          <div className="text-center text-slate-450 dark:text-slate-600 py-12 italic">
            No audited document clauses loaded.
          </div>
        ) : (
          Object.keys(pages).map((pageNumStr) => {
            const pageNum = parseInt(pageNumStr);
            const pageClauses = pages[pageNum];
            return (
              <div key={pageNum} className="space-y-4">
                {/* Page Divider marker */}
                <div className="flex items-center justify-center gap-2 select-none">
                  <div className="flex-1 h-[1px] bg-slate-200 dark:bg-slate-850" />
                  <span className="text-[10px] font-extrabold text-slate-400 dark:text-slate-500 uppercase tracking-widest bg-slate-100 dark:bg-slate-900 px-3 py-1 rounded-full border border-slate-200 dark:border-slate-800">
                    Page {pageNum}
                  </span>
                  <div className="flex-1 h-[1px] bg-slate-200 dark:bg-slate-850" />
                </div>

                {/* Clauses on page */}
                <div className="space-y-3.5">
                  {pageClauses.map((c) => {
                    const isSelected = selectedClauseId === c.chunk_id;
                    return (
                      <div
                        key={c.chunk_id}
                        ref={(el) => {
                          clauseRefs.current[c.chunk_id] = el;
                        }}
                        onClick={() => onSelectClause(c.chunk_id)}
                        className={`p-4 rounded-xl border transition-all duration-300 cursor-pointer ${getHeatmapColor(
                          c.risk_level,
                          isSelected
                        )}`}
                      >
                        <div className="flex items-start justify-between gap-4 mb-2 select-none">
                          <span className={`text-[10px] font-black uppercase tracking-wider ${getLabelColor(c.risk_level)}`}>
                            {c.risk_category} • {c.risk_level} Risk (Score: {c.risk_score.toFixed(1)})
                          </span>
                          <span className="text-[9px] font-bold text-slate-400 dark:text-slate-500 font-mono">
                            Page {c.page_num} • Block {c.block_num}
                          </span>
                        </div>
                        <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-normal">
                          {c.text}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
