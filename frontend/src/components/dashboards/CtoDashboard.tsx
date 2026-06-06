"use client";

import React from "react";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar
} from "recharts";
import { 
  TrendingUp, 
  Hourglass, 
  DollarSign, 
  Heart,
  Calendar,
  Zap,
  Activity,
  GitPullRequest
} from "lucide-react";

// Mock trend history
const trendData = [
  { date: "May 30", critical: 4, high: 8, medium: 15, low: 25 },
  { date: "May 31", critical: 4, high: 7, medium: 14, low: 22 },
  { date: "Jun 01", critical: 3, high: 7, medium: 13, low: 20 },
  { date: "Jun 02", critical: 3, high: 6, medium: 11, low: 18 },
  { date: "Jun 03", critical: 2, high: 5, medium: 12, low: 18 },
  { date: "Jun 04", critical: 2, high: 5, medium: 10, low: 15 },
  { date: "Jun 05", critical: 2, high: 3, medium: 8, low: 12 },
];

const debtData = [
  { module: "Auth", hours: 24, cost: 2400 },
  { module: "Ingestion", hours: 45, cost: 4500 },
  { module: "Agents", hours: 12, cost: 1200 },
  { module: "GraphRAG", hours: 18, cost: 1800 },
  { module: "Frontend", hours: 30, cost: 3000 },
];

export default function CtoDashboard() {
  return (
    <div className="flex flex-col gap-6 w-full">
      {/* Bento Dials Header */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Code Health */}
        <div className="glass-panel rounded-xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono">CODE HEALTH SCORE</span>
            <Heart className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-display font-bold text-emerald-400 glow-primary">84.2</span>
            <span className="text-xs text-slate-500">Grade B+</span>
          </div>
          <div className="text-[10px] text-slate-500 font-mono mt-2">
            Up 4.1% over last 30 days
          </div>
        </div>

        {/* Tech Debt Hours */}
        <div className="glass-panel rounded-xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono">TECH DEBT BURDEN</span>
            <Hourglass className="w-4 h-4 text-amber-500" />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-display font-bold text-amber-500">129 hrs</span>
            <span className="text-xs text-slate-500">Remediation</span>
          </div>
          <div className="text-[10px] text-slate-500 font-mono mt-2">
            Est. engineering effort required
          </div>
        </div>

        {/* Refactoring ROI */}
        <div className="glass-panel rounded-xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono">AUTO-FIX REFACTORING ROI</span>
            <DollarSign className="w-4 h-4 text-teal-400" />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-display font-bold text-teal-400">$12,900</span>
            <span className="text-xs text-slate-500">Saved</span>
          </div>
          <div className="text-[10px] text-slate-500 font-mono mt-2">
            Calculated from 43 auto-remediations
          </div>
        </div>

        {/* Deploy Velocity */}
        <div className="glass-panel rounded-xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono">MTTR (MEAN TIME TO RECOVER)</span>
            <Zap className="w-4 h-4 text-primary" />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-display font-bold text-primary">1.8 hrs</span>
            <span className="text-xs text-slate-500">Average</span>
          </div>
          <div className="text-[10px] text-slate-500 font-mono mt-2">
            Industry Benchmark: Elite (&lt; 1 hr)
          </div>
        </div>
      </div>

      {/* Charts Bento grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Area Chart */}
        <div className="lg:col-span-2 glass-panel rounded-xl p-6 flex flex-col gap-4">
          <div>
            <h3 className="font-semibold text-slate-200">Vulnerability Incidence Trends</h3>
            <span className="text-xs text-slate-500">Historical view of active vulnerability findings by severity</span>
          </div>

          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCrit" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorHigh" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorMed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#eab308" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#eab308" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip 
                  contentStyle={{ backgroundColor: "#0b0f17", border: "1px solid rgba(255,255,255,0.08)" }}
                  labelStyle={{ color: "#94a3b8" }}
                />
                <Area type="monotone" dataKey="critical" stroke="#f43f5e" fillOpacity={1} fill="url(#colorCrit)" />
                <Area type="monotone" dataKey="high" stroke="#f97316" fillOpacity={1} fill="url(#colorHigh)" />
                <Area type="monotone" dataKey="medium" stroke="#eab308" fillOpacity={1} fill="url(#colorMed)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Debt By Module Bar Chart */}
        <div className="lg:col-span-1 glass-panel rounded-xl p-6 flex flex-col gap-4">
          <div>
            <h3 className="font-semibold text-slate-200">Tech Debt Concentration</h3>
            <span className="text-xs text-slate-500">Refactoring cost ($) and effort by package module</span>
          </div>

          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={debtData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="module" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0b0f17", border: "1px solid rgba(255,255,255,0.08)" }}
                  labelStyle={{ color: "#94a3b8" }}
                />
                <Bar dataKey="cost" fill="#10b981" radius={[4, 4, 0, 0]} name="Est Cost ($)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* DORA Metrics Panel */}
      <div className="glass-panel rounded-xl p-6 flex flex-col gap-4">
        <div>
          <h3 className="font-semibold text-slate-200">DORA Metrics Scorecard</h3>
          <span className="text-xs text-slate-500">DevOps Research and Assessment engineering benchmarks</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-2">
          <div className="bg-slate-900/40 border border-white/5 rounded-lg p-4">
            <div className="text-xs text-slate-500 font-mono mb-1">DEPLOYMENT FREQUENCY</div>
            <div className="text-xl font-bold text-slate-200">Multiple / Day</div>
            <div className="text-[10px] text-emerald-400 font-mono mt-1">ELITE</div>
          </div>
          <div className="bg-slate-900/40 border border-white/5 rounded-lg p-4">
            <div className="text-xs text-slate-500 font-mono mb-1">LEAD TIME FOR CHANGES</div>
            <div className="text-xl font-bold text-slate-200">&lt; 24 Hours</div>
            <div className="text-[10px] text-emerald-400 font-mono mt-1">ELITE</div>
          </div>
          <div className="bg-slate-900/40 border border-white/5 rounded-lg p-4">
            <div className="text-xs text-slate-500 font-mono mb-1">CHANGE FAILURE RATE</div>
            <div className="text-xl font-bold text-slate-200">4.2%</div>
            <div className="text-[10px] text-emerald-400 font-mono mt-1">ELITE</div>
          </div>
          <div className="bg-slate-900/40 border border-white/5 rounded-lg p-4">
            <div className="text-xs text-slate-500 font-mono mb-1">TIME TO RESTORE SERVICE</div>
            <div className="text-xl font-bold text-slate-200">1.8 Hours</div>
            <div className="text-[10px] text-primary font-mono mt-1">HIGH</div>
          </div>
        </div>
      </div>
    </div>
  );
}
