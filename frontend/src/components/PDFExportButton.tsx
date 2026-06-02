"use client";

import React, { useState } from "react";
import { Download, AlertTriangle } from "lucide-react";
import { API_BASE_URL } from "../lib/api";

interface PDFExportButtonProps {
  jobId: string;
}

export default function PDFExportButton({ jobId }: PDFExportButtonProps) {
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePdfDownload = async () => {
    setDownloading(true);
    setError(null);
    try {
      const url = `${API_BASE_URL}/report/${jobId}/pdf`;
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Server returned status code ${response.status}. PDF might not be generated yet.`);
      }
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.setAttribute("download", `Legal_Risk_Report_${jobId.slice(0, 8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (e: any) {
      setError(e.message || "Failed to download PDF.");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="flex flex-col items-stretch gap-2 w-full">
      <button
        onClick={handlePdfDownload}
        disabled={downloading}
        className="w-full bg-gradient-to-r from-sky-600 to-sky-700 hover:from-sky-500 hover:to-sky-600 text-white font-bold py-3 px-6 rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-sky-500/10 active:scale-[0.98] transition-all disabled:opacity-50 disabled:pointer-events-none"
      >
        {downloading ? (
          <>
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Compiling Brief PDF...
          </>
        ) : (
          <>
            <Download className="w-4.5 h-4.5" />
            Export Executive PDF
          </>
        )}
      </button>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-650 dark:text-red-400 text-[10px] p-2.5 rounded-lg flex items-center gap-1.5 font-bold uppercase tracking-wide">
          <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
