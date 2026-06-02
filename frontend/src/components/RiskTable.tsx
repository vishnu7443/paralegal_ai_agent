"use client";

import React, { useState } from "react";
import { AlertCircle, ArrowUpDown, ShieldAlert, FileText } from "lucide-react";
import { Clause } from "../lib/types";

interface RiskTableProps {
  clauses: Clause[];
  selectedClauseId: number | null;
  onSelectClause: (clauseId: number) => void;
}

type SortKey = "page_num" | "risk_score" | "risk_category";
type SortOrder = "asc" | "desc";

export default function RiskTable({ clauses, selectedClauseId, onSelectClause }: RiskTableProps) {
  const [filterLevel, setFilterLevel] = useState<string>("ALL");
  const [sortKey, setSortKey] = useState<SortKey>("risk_score");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  // Filtering
  const filteredClauses = clauses.filter((c) => {
    if (filterLevel === "ALL") return true;
    return c.risk_level.toUpperCase() === filterLevel;
  });

  // Sorting
  const sortedClauses = [...filteredClauses].sort((a, b) => {
    let valA = a[sortKey];
    let valB = b[sortKey];

    if (typeof valA === "string" && typeof valB === "string") {
      return sortOrder === "asc"
        ? valA.localeCompare(valB)
        : valB.localeCompare(valA);
    } else if (typeof valA === "number" && typeof valB === "number") {
      return sortOrder === "asc" ? valA - valB : valB - valA;
    }
    return 0;
  });

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortOrder("desc");
    }
  };

  const getRiskBadgeStyles = (level: string) => {
    switch (level) {
      case "Critical":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400 border-purple-500/20";
      case "High":
        return "bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400 border-rose-500/20";
      case "Medium":
        return "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400 border-amber-500/20";
      default:
        return "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400 border-emerald-500/20";
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-md overflow-hidden shadow-md flex flex-col h-full">
      {/* Filtering Header Panel */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-slate-50/50 dark:bg-slate-900/25">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-sky-500" />
          <h3 className="font-bold text-sm text-slate-800 dark:text-slate-100">
            Flagged Risk Clauses ({filteredClauses.length})
          </h3>
        </div>
        
        {/* Filters */}
        <div className="flex items-center gap-1.5 self-stretch sm:self-auto select-none">
          {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((level) => (
            <button
              key={level}
              onClick={() => setFilterLevel(level)}
              className={`px-2.5 py-1 rounded-lg text-[10px] font-extrabold uppercase border transition-all ${
                filterLevel === level
                  ? "bg-slate-850 border-slate-850 text-white dark:bg-slate-100 dark:border-slate-100 dark:text-slate-900"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-350 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-400 dark:hover:border-slate-700"
              }`}
            >
              {level}
            </button>
          ))}
        </div>
      </div>

      {/* Risk Table list */}
      <div className="overflow-x-auto flex-1 max-h-[480px]">
        <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-left text-xs leading-normal">
          <thead className="bg-slate-50/30 dark:bg-slate-900/10 font-bold uppercase tracking-wider text-[10px] text-slate-400 dark:text-slate-500 sticky top-0 backdrop-blur-md border-b border-slate-200 dark:border-slate-850">
            <tr>
              <th
                onClick={() => toggleSort("page_num")}
                className="px-4 py-3 cursor-pointer hover:text-slate-650 dark:hover:text-slate-300 select-none w-16"
              >
                <div className="flex items-center gap-1">
                  Page <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => toggleSort("risk_category")}
                className="px-4 py-3 cursor-pointer hover:text-slate-650 dark:hover:text-slate-300 select-none"
              >
                <div className="flex items-center gap-1">
                  Category <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => toggleSort("risk_score")}
                className="px-4 py-3 cursor-pointer hover:text-slate-650 dark:hover:text-slate-300 select-none w-20 text-center"
              >
                <div className="flex items-center gap-1 justify-center">
                  Score <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="px-4 py-3">Clause Snippet &amp; Exposure</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-150 dark:divide-slate-900/40 font-medium">
            {sortedClauses.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-12 text-center text-slate-400 dark:text-slate-600 italic">
                  No clauses matching the selected risk level filter.
                </td>
              </tr>
            ) : (
              sortedClauses.map((c) => {
                const isSelected = selectedClauseId === c.chunk_id;
                return (
                  <tr
                    key={c.chunk_id}
                    onClick={() => onSelectClause(c.chunk_id)}
                    className={`cursor-pointer transition-colors ${
                      isSelected
                        ? "bg-sky-500/10 hover:bg-sky-500/15 border-l-4 border-l-sky-500"
                        : "hover:bg-slate-100/50 dark:hover:bg-slate-900/20"
                    }`}
                  >
                    <td className="px-4 py-4.5 font-bold font-mono">Page {c.page_num}</td>
                    <td className="px-4 py-4.5 font-semibold text-slate-800 dark:text-slate-200">
                      {c.risk_category}
                    </td>
                    <td className="px-4 py-4.5 text-center">
                      <span className={`px-2 py-0.5 rounded border text-[10px] font-black uppercase ${getRiskBadgeStyles(c.risk_level)}`}>
                        {c.risk_score.toFixed(1)}
                      </span>
                    </td>
                    <td className="px-4 py-4.5 text-slate-600 dark:text-slate-350 pr-6">
                      <p className="line-clamp-2 font-normal text-slate-750 dark:text-slate-300 leading-normal mb-1">
                        {c.text}
                      </p>
                      <p className="text-[10px] font-bold text-slate-400 dark:text-slate-550 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3 text-sky-500" />
                        {c.risk_explanation}
                      </p>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
