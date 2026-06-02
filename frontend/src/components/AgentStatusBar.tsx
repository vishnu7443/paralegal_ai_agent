"use client";

import React, { useEffect, useRef } from "react";
import { Terminal, CheckCircle2, PlayCircle, Clock, ShieldAlert } from "lucide-react";
import { AgentLog } from "../lib/types";

interface AgentStatusBarProps {
  logs: AgentLog[];
  jobStatus: string;
}

export default function AgentStatusBar({ logs, jobStatus }: AgentStatusBarProps) {
  const terminalEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll terminal logs to the bottom
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // Determine individual agent states based on incoming logs and job status
  const getAgentStatus = (agentName: string) => {
    const agentLogs = logs.filter(l => l.agent === agentName);
    
    if (agentLogs.length === 0) {
      if (jobStatus === "FAILED") return "failed";
      return "pending";
    }
    
    const isCompleted = agentLogs.some(l => l.phase === "COMPLETE" || l.phase === "FAILED");
    if (isCompleted) {
      const isFailed = agentLogs.some(l => l.phase === "FAILED");
      return isFailed ? "failed" : "completed";
    }
    
    return "running";
  };

  const agents = [
    {
      id: "ClauseAgent",
      name: "Clause Extraction Agent",
      desc: "Runs semantic RAG queries to extract risk-relevant clauses",
      status: getAgentStatus("ClauseAgent"),
    },
    {
      id: "MetadataAgent",
      name: "Contract Metadata Agent",
      desc: "Scans for governing law, jurisdiction, and dates in parallel",
      status: getAgentStatus("MetadataAgent"),
    },
    {
      id: "RiskAgent",
      name: "Risk Scorer Agent",
      desc: "Cross-references clauses against risk lexicon weights",
      status: getAgentStatus("RiskAgent"),
    },
    {
      id: "ReportAgent",
      name: "Generative Analysis Agent",
      desc: "Synthesizes multi-agent state into legal report stream",
      status: getAgentStatus("ReportAgent"),
    },
  ];

  return (
    <div className="space-y-6">
      {/* 4-Agent Grid State Visualizer */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {agents.map((a, idx) => (
          <div
            key={idx}
            className={`p-5 rounded-2xl border transition-all duration-300 backdrop-blur-md ${
              a.status === "running"
                ? "border-sky-500/30 bg-sky-500/5 ring-1 ring-sky-500/10 shadow-lg shadow-sky-500/5"
                : a.status === "completed"
                ? "border-emerald-500/20 dark:border-emerald-500/10 bg-emerald-500/5"
                : a.status === "failed"
                ? "border-red-500/20 bg-red-500/5"
                : "border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50"
            }`}
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-bold text-sm tracking-tight text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
                  {a.name}
                </h3>
                <p className="text-xs text-slate-400 dark:text-slate-500 mt-1 leading-relaxed">
                  {a.desc}
                </p>
              </div>
              <div className="mt-0.5">
                {a.status === "completed" ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                ) : a.status === "running" ? (
                  <div className="relative flex items-center justify-center">
                    <span className="w-3.5 h-3.5 bg-sky-500 rounded-full animate-ping absolute" />
                    <PlayCircle className="w-5 h-5 text-sky-500 relative z-10" />
                  </div>
                ) : a.status === "failed" ? (
                  <ShieldAlert className="w-5 h-5 text-red-500" />
                ) : (
                  <Clock className="w-5 h-5 text-slate-300 dark:text-slate-700" />
                )}
              </div>
            </div>

            {/* Micro loading progress animation */}
            {a.status === "running" && (
              <div className="w-full bg-slate-200/50 h-1 rounded-full overflow-hidden mt-4 dark:bg-slate-800">
                <div className="bg-sky-500 h-1 rounded-full w-2/3 animate-pulse" />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Terminal Reasonings Feed Console */}
      <div className="rounded-2xl overflow-hidden border border-slate-900 bg-[#090d16] text-[#c9d1d9] shadow-2xl relative font-mono text-[11px] leading-relaxed">
        {/* Terminal Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-[#0d1117] border-b border-slate-800/80">
          <div className="flex items-center space-x-2">
            <div className="flex space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500/70" />
              <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/70" />
              <span className="w-2.5 h-2.5 rounded-full bg-green-500/70" />
            </div>
            <span className="text-[10px] font-bold tracking-wider text-slate-500 uppercase flex items-center gap-1.5 pl-2">
              <Terminal className="w-3.5 h-3.5 text-slate-500" />
              Agent Console Output
            </span>
          </div>
          
          <div className="flex items-center space-x-3 text-[9px] text-slate-600 font-bold uppercase tracking-widest">
            <span>Shell: PS_CORE</span>
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          </div>
        </div>

        {/* Console logs area */}
        <div className="p-4 h-56 overflow-y-auto terminal-scroll space-y-2 flex flex-col">
          {logs.length === 0 ? (
            <div className="text-slate-500 flex flex-col items-center justify-center h-full gap-2 italic">
              <span className="animate-pulse">Waiting for Agent Crew signals...</span>
            </div>
          ) : (
            logs.map((l, idx) => {
              const isErr = l.message.includes("ERROR") || l.phase === "FAILED";
              const phaseColor =
                l.phase === "THINK"
                  ? "text-purple-400"
                  : l.phase === "DECIDE"
                  ? "text-sky-400"
                  : l.phase === "ACT"
                  ? "text-yellow-400 font-medium"
                  : l.phase === "OBSERVE"
                  ? "text-emerald-400"
                  : "text-slate-350";

              const agentColor =
                l.agent === "ClauseAgent"
                  ? "text-sky-500"
                  : l.agent === "MetadataAgent"
                  ? "text-teal-400"
                  : l.agent === "RiskAgent"
                  ? "text-emerald-500"
                  : "text-purple-500";

              return (
                <div key={idx} className="flex items-start gap-2 hover:bg-slate-900/40 py-0.5 rounded px-1 transition-colors">
                  <span className="text-slate-650 select-none">[{l.timestamp ? new Date(l.timestamp).toLocaleTimeString() : "--:--:--"}]</span>
                  <span className={`${agentColor} font-bold select-none`}>[{l.agent}]</span>
                  <span className={`${phaseColor} font-black select-none`}>[{l.phase}]</span>
                  <span className={`${isErr ? "text-red-400 font-semibold" : "text-slate-200"}`}>
                    {l.message}
                  </span>
                </div>
              );
            })
          )}
          <div ref={terminalEndRef} />
        </div>
      </div>
    </div>
  );
}
