"use client";

import React from "react";
import { FileText, Download } from "lucide-react";

interface StreamingReportProps {
  markdown: string;
  isComplete: boolean;
  onDownloadPdf?: () => void;
}

export default function StreamingReport({ markdown, isComplete, onDownloadPdf }: StreamingReportProps) {
  
  // Custom lightweight parser that transforms standard markdown lines into beautifully styled React elements
  const parseMarkdownToJSX = (text: string) => {
    if (!text) {
      return (
        <div className="text-slate-400 dark:text-slate-650 flex flex-col items-center justify-center py-12 gap-3 italic">
          <span className="w-6 h-6 border-2 border-slate-400 border-t-transparent rounded-full animate-spin dark:border-slate-600" />
          <span>Synthesizing qualitative legal brief...</span>
        </div>
      );
    }

    const lines = text.split("\n");
    let inTable = false;
    let tableHeaders: string[] = [];
    let tableRows: string[][] = [];

    const elements: React.ReactNode[] = [];

    const renderText = (str: string) => {
      let cleanText = str;
      const combinedRegex = /(\*\*|`)(.*?)\1/g;
      const parts: React.ReactNode[] = [];
      let lastIndex = 0;
      let match;
      
      while ((match = combinedRegex.exec(cleanText)) !== null) {
        const index = match.index;
        const tag = match[1];
        const content = match[2];

        if (index > lastIndex) {
          parts.push(cleanText.substring(lastIndex, index));
        }

        if (tag === "**") {
          parts.push(<strong key={index} className="font-extrabold text-slate-900 dark:text-slate-50">{content}</strong>);
        } else if (tag === "`") {
          parts.push(<code key={index} className="bg-slate-100 text-slate-800 dark:bg-slate-950 dark:text-slate-300 font-mono text-xs px-1.5 py-0.5 rounded">{content}</code>);
        }

        lastIndex = combinedRegex.lastIndex;
      }

      if (lastIndex < cleanText.length) {
        parts.push(cleanText.substring(lastIndex));
      }

      return parts.length > 0 ? parts : cleanText;
    };

    lines.forEach((line, index) => {
      const trimmed = line.trim();

      // Table parsing
      if (trimmed.startsWith("|")) {
        inTable = true;
        const cells = trimmed.split("|").map(c => c.trim()).filter(c => c !== "");
        
        // If it's a spacer row e.g. |:---|:---|
        if (cells.every(c => c.startsWith(":") || c.startsWith("-"))) {
          return;
        }

        if (tableHeaders.length === 0) {
          tableHeaders = cells;
        } else {
          tableRows.push(cells);
        }
        return;
      } else if (inTable && !trimmed.startsWith("|")) {
        // Table finished, render table element
        elements.push(
          <div key={`table-${index}`} className="overflow-x-auto my-6 border border-slate-200 dark:border-slate-800 rounded-xl">
            <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-left text-sm leading-relaxed">
              <thead className="bg-slate-50 dark:bg-slate-900/60 font-bold uppercase tracking-wider text-[11px] text-slate-400 dark:text-slate-500">
                <tr>
                  {tableHeaders.map((h, i) => (
                    <th key={i} className="px-4 py-3.5 first:pl-6">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-900/40 font-medium">
                {tableRows.map((row, rowIdx) => (
                  <tr key={rowIdx} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/10">
                    {row.map((cell, cellIdx) => (
                      <td key={cellIdx} className="px-4 py-3 first:pl-6 text-slate-700 dark:text-slate-350">{renderText(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        inTable = false;
        tableHeaders = [];
        tableRows = [];
      }

      if (trimmed === "") {
        return;
      }

      // Headers
      if (trimmed.startsWith("# ")) {
        elements.push(
          <h1 key={index} className="text-2xl font-extrabold tracking-tight mt-8 mb-4 border-b border-slate-200 dark:border-slate-800 pb-2 text-slate-900 dark:text-slate-50">
            {trimmed.substring(2)}
          </h1>
        );
      } else if (trimmed.startsWith("## ")) {
        elements.push(
          <h2 key={index} className="text-xl font-extrabold tracking-tight mt-6 mb-3 text-slate-900 dark:text-slate-100">
            {trimmed.substring(3)}
          </h2>
        );
      } else if (trimmed.startsWith("### ")) {
        elements.push(
          <h3 key={index} className="text-md font-bold tracking-tight mt-4 mb-2 text-sky-650 dark:text-sky-400">
            {trimmed.substring(4)}
          </h3>
        );
      }
      // Blockquotes
      else if (trimmed.startsWith("> ")) {
        elements.push(
          <blockquote key={index} className="border-l-4 border-sky-500 pl-4 py-1 my-3 bg-slate-50 dark:bg-slate-900/30 rounded-r-lg italic text-sm text-slate-650 dark:text-slate-350 leading-relaxed">
            {renderText(trimmed.substring(2))}
          </blockquote>
        );
      }
      // Bullets
      else if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
        elements.push(
          <ul key={index} className="list-disc pl-5 my-2 space-y-1">
            <li className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
              {renderText(trimmed.substring(2))}
            </li>
          </ul>
        );
      }
      // Numbered List
      else if (/^\d+\.\s/.test(trimmed)) {
        const content = trimmed.replace(/^\d+\.\s/, "");
        elements.push(
          <ol key={index} className="list-decimal pl-5 my-2 space-y-1">
            <li className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
              {renderText(content)}
            </li>
          </ol>
        );
      }
      // Paragraph
      else {
        elements.push(
          <p key={index} className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed my-3 font-normal">
            {renderText(trimmed)}
          </p>
        );
      }
    });

    // Render outstanding table if file ended on table
    if (inTable && tableHeaders.length > 0) {
      elements.push(
        <div key="table-end" className="overflow-x-auto my-6 border border-slate-200 dark:border-slate-800 rounded-xl">
          <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-left text-sm leading-relaxed">
            <thead className="bg-slate-50 dark:bg-slate-900/60 font-bold uppercase tracking-wider text-[11px] text-slate-400 dark:text-slate-500">
              <tr>
                {tableHeaders.map((h, i) => (
                  <th key={i} className="px-4 py-3.5 first:pl-6">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-900/40 font-medium">
              {tableRows.map((row, rowIdx) => (
                <tr key={rowIdx} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/10">
                  {row.map((cell, cellIdx) => (
                    <td key={cellIdx} className="px-4 py-3 first:pl-6 text-slate-700 dark:text-slate-350">{renderText(cell)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    return elements;
  };

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-900/60 backdrop-blur-md shadow-xl overflow-hidden mt-6">
      {/* Report Header Panel */}
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-900/40">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-sky-500" />
          <span className="font-bold text-sm text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
            Legal Analysis Report
            {!isComplete && (
              <span className="flex items-center gap-1 bg-sky-550/10 text-sky-600 text-[10px] font-bold uppercase tracking-widest border border-sky-500/25 px-2 py-0.5 rounded-full dark:text-sky-400 dark:bg-sky-550/5">
                <span className="w-1.5 h-1.5 rounded-full bg-sky-500 animate-ping" />
                Streaming...
              </span>
            )}
          </span>
        </div>
        
        {isComplete && onDownloadPdf && (
          <button
            onClick={onDownloadPdf}
            className="flex items-center gap-1.5 text-xs font-bold bg-sky-600 hover:bg-sky-550 text-white px-3.5 py-2 rounded-xl transition-all shadow-md shadow-sky-500/10 hover:shadow-sky-500/20 active:scale-95"
          >
            <Download className="w-3.5 h-3.5" />
            Download PDF Report
          </button>
        )}
      </div>

      {/* Styled Markdown content */}
      <div className="p-6 md:p-8 max-w-none text-slate-800 dark:text-slate-250 select-text prose prose-slate dark:prose-invert">
        {parseMarkdownToJSX(markdown)}
      </div>
    </div>
  );
}
