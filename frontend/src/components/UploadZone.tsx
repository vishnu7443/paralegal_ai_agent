"use client";

import React, { useState, useRef } from "react";
import { UploadCloud, File, AlertCircle, CheckCircle } from "lucide-react";
import { uploadDocument } from "../lib/api";

interface UploadZoneProps {
  onUploadSuccess: (docId: number, filename: string) => void;
}

export default function UploadZone({ onUploadSuccess }: UploadZoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const processFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported.");
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);
    setProgress(20);

    const timer = setInterval(() => {
      setProgress((prev) => (prev < 80 ? prev + 15 : prev));
    }, 400);

    try {
      const res = await uploadDocument(file);
      clearInterval(timer);
      setProgress(100);
      setSuccess(`Successfully uploaded and indexed '${file.name}'`);
      
      // Delay to let user see 100% progress
      setTimeout(() => {
        setUploading(false);
        onUploadSuccess(res.document_id, res.filename);
      }, 800);
    } catch (e: any) {
      clearInterval(timer);
      setUploading(false);
      setError(e.message || "Failed to process PDF contract.");
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await processFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      await processFile(e.target.files[0]);
    }
  };

  const onButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full">
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={!uploading ? onButtonClick : undefined}
        className={`w-full p-8 rounded-2xl border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center cursor-pointer text-center relative overflow-hidden bg-white/50 dark:bg-slate-900/50 backdrop-blur-md ${
          isDragActive
            ? "border-sky-500 bg-sky-500/5"
            : uploading
            ? "border-sky-300 bg-sky-50/10 cursor-not-allowed"
            : "border-slate-300 dark:border-slate-800 hover:border-sky-500 hover:bg-slate-50/50 dark:hover:bg-slate-900/40"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf"
          onChange={handleChange}
          disabled={uploading}
        />

        {uploading ? (
          <div className="w-full max-w-xs space-y-4 py-4">
            <UploadCloud className="w-10 h-10 text-sky-500 animate-bounce mx-auto" />
            <div className="space-y-1.5">
              <p className="text-sm font-bold text-slate-800 dark:text-slate-100">
                Extracting &amp; Indexing Contract...
              </p>
              <p className="text-xs text-slate-400 dark:text-slate-500 font-mono">
                {progress}% complete
              </p>
            </div>
            
            <div className="w-full bg-slate-200 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-sky-500 h-1.5 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="p-3 bg-sky-500/10 text-sky-600 rounded-full w-fit mx-auto border border-sky-500/20">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-bold text-slate-800 dark:text-slate-100">
                Drag &amp; drop your PDF contract here
              </p>
              <p className="text-xs text-slate-400 dark:text-slate-500">
                or click to browse local files (PDF only, max 15MB)
              </p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-3 bg-red-500/10 border border-red-550/20 text-red-655 dark:text-red-400 p-3 rounded-xl flex items-start gap-2.5 text-xs font-medium">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="mt-3 bg-emerald-500/10 border border-emerald-550/20 text-emerald-655 dark:text-emerald-400 p-3 rounded-xl flex items-start gap-2.5 text-xs font-medium">
          <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}
    </div>
  );
}
