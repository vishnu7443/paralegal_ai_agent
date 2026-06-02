"use client";

import React, { useEffect, useState } from "react";
import { Shield } from "lucide-react";

interface RiskGaugeProps {
  score: number; // 1 to 10
}

export default function RiskGauge({ score }: RiskGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);

  // Trigger smooth pointer needle entry sweep animation
  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedScore(score);
    }, 150);
    return () => clearTimeout(timer);
  }, [score]);

  // SVG dimensions
  const width = 200;
  const height = 120;
  const radius = 80;
  const cx = width / 2;
  const cy = height - 10;
  
  // Calculate needle coordinates
  // Range is 180 degrees (from Left to Right)
  // 1 -> 180 degrees (Math.PI)
  // 10 -> 0 degrees (0)
  const scorePercent = Math.max(0, Math.min(1, (animatedScore - 1) / 9)); // 0 to 1
  const angle = Math.PI - (scorePercent * Math.PI); // Angle in radians
  
  const needleLength = radius - 15;
  const needleX = cx + needleLength * Math.cos(angle);
  const needleY = cy - needleLength * Math.sin(angle);

  // Determine risk categories
  const getRiskLabel = (s: number) => {
    if (s < 4.0) return { text: "Low Threat", color: "text-emerald-500", bg: "bg-emerald-500/10 border-emerald-500/20" };
    if (s < 7.0) return { text: "Medium Threat", color: "text-amber-500", bg: "bg-amber-500/10 border-amber-500/20" };
    if (s < 9.0) return { text: "High Threat", color: "text-rose-500", bg: "bg-rose-500/10 border-rose-500/20" };
    return { text: "Critical Threat", color: "text-purple-500", bg: "bg-purple-500/10 border-purple-500/20" };
  };

  const labelInfo = getRiskLabel(score);

  return (
    <div className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-md flex flex-col items-center justify-between h-full shadow-md">
      <div className="w-full text-left self-start">
        <h3 className="font-bold text-base text-slate-900 dark:text-slate-50 flex items-center gap-2">
          <Shield className="w-5 h-5 text-sky-500" />
          Overall Risk Rating
        </h3>
        <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5 mb-2">
          Contract threat index based on clause severity.
        </p>
      </div>

      {/* SVG Arc Gauge */}
      <div className="relative select-none my-4">
        <svg width={width} height={height} className="overflow-visible">
          <defs>
            {/* Emerald to Orange to Red metallic gradient */}
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" />   {/* Emerald 500 */}
              <stop offset="50%" stopColor="#f59e0b" />  {/* Amber 500 */}
              <stop offset="80%" stopColor="#f43f5e" />  {/* Rose 500 */}
              <stop offset="100%" stopColor="#8b5cf6" /> {/* Purple 550 */}
            </linearGradient>
            <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.15" />
            </filter>
          </defs>
          
          {/* Background track arc */}
          <path
            d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
            fill="none"
            stroke="var(--border, #cbd5e1)"
            strokeWidth="12"
            strokeLinecap="round"
            style={{ opacity: 0.2 }}
          />

          {/* Color filled track arc */}
          <path
            d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth="12"
            strokeLinecap="round"
          />

          {/* Center cap anchor */}
          <circle cx={cx} cy={cy} r="8" className="fill-slate-800 dark:fill-slate-200" />
          <circle cx={cx} cy={cy} r="4" className="fill-white dark:fill-slate-900" />

          {/* Sweeping pointer needle */}
          <line
            x1={cx}
            y1={cy}
            x2={needleX}
            y2={needleY}
            className="stroke-slate-800 dark:stroke-slate-200"
            strokeWidth="3.5"
            strokeLinecap="round"
            filter="url(#shadow)"
            style={{ transition: "all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)" }}
          />
        </svg>

        {/* Center Score badge */}
        <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 flex flex-col items-center">
          <span className="text-3xl font-black tracking-tight text-slate-800 dark:text-slate-100">{score.toFixed(1)}</span>
          <span className="text-[9px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest block -mt-1">
            Contract Score
          </span>
        </div>
      </div>

      {/* Description tag */}
      <div className={`mt-2 px-4 py-1.5 rounded-xl border text-xs font-extrabold uppercase tracking-wider ${labelInfo.bg} ${labelInfo.color}`}>
        {labelInfo.text}
      </div>
    </div>
  );
}
