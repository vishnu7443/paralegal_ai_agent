"use client";

import { useEffect, useState } from "react";
import { AgentLog } from "../lib/types";

export function useSSE(jobId: string | null) {
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [reportMarkdown, setReportMarkdown] = useState<string>("");
  const [jobStatus, setJobStatus] = useState<string>("PENDING");
  const [isComplete, setIsComplete] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;

    setLogs([]);
    setReportMarkdown("");
    setJobStatus("PENDING");
    setIsComplete(false);
    setError(null);

    // Proxy SSE route through Next.js or connect directly to FastAPI
    // Since CORS is enabled on FastAPI, direct connection works flawlessly
    const sseUrl = `http://localhost:8000/api/stream/${jobId}`;
    console.log(`[useSSE] Subscribing to SSE channel at: ${sseUrl}`);
    
    const eventSource = new EventSource(sseUrl);

    eventSource.onopen = () => {
      console.log("[useSSE] SSE stream connection established.");
      setJobStatus("RUNNING");
    };

    eventSource.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        
        // Handle token event (Gemini report stream)
        if (parsed.type === "token") {
          setReportMarkdown((prev) => prev + parsed.content);
        }
        // Handle completed status event
        else if (parsed.type === "status" && parsed.content === "COMPLETE") {
          console.log("[useSSE] Agent crew completed process.");
          setJobStatus("COMPLETED");
          setIsComplete(true);
          eventSource.close();
        }
        // Handle agent reasoning logs
        else if (parsed.agent) {
          setLogs((prev) => {
            // Avoid duplicate log insertions
            const exists = prev.some(
              (l) => l.agent === parsed.agent && l.phase === parsed.phase && l.message === parsed.message
            );
            if (exists) return prev;
            return [...prev, parsed as AgentLog];
          });

          if (parsed.agent === "Orchestrator" && parsed.phase === "FAILED") {
            setJobStatus("FAILED");
            setError(parsed.message || "Execution failed.");
            eventSource.close();
          }
        }
      } catch (err) {
        console.error("[useSSE] Failed to parse SSE event data:", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("[useSSE] SSE connection dropped or failed:", err);
      // We don't close immediately in case of transient reconnects,
      // but we signal the potential error state.
    };

    return () => {
      eventSource.close();
      console.log("[useSSE] SSE connection closed.");
    };
  }, [jobId]);

  return {
    logs,
    reportMarkdown,
    jobStatus,
    isComplete,
    error,
    setReportMarkdown,
    setJobStatus,
    setIsComplete
  };
}
