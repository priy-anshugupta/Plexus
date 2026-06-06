"use client";

import React from "react";
import { 
  LayoutDashboard, 
  GitFork, 
  SearchCode, 
  ShieldAlert, 
  Settings,
  Flame,
  Binary
} from "lucide-react";

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export default function Sidebar({ activeTab, setActiveTab }: SidebarProps) {
  const menuItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "repos", label: "Repositories", icon: GitFork },
    { id: "scans", label: "Scans", icon: SearchCode },
    { id: "findings", label: "Findings", icon: ShieldAlert },
    { id: "explorer", label: "Code Explorer", icon: Binary },
  ];

  return (
    <aside className="w-64 bg-panel-dark/40 border-r border-white/5 flex flex-col justify-between p-4 min-h-screen sticky top-0">
      <div className="flex flex-col gap-8">
        {/* Brand Logo */}
        <div className="flex items-center gap-3 px-2 py-3">
          <div className="bg-primary/10 p-2 rounded-lg border border-primary/20">
            <Flame className="w-6 h-6 text-primary glow-primary" />
          </div>
          <div>
            <h1 className="font-display font-bold text-xl tracking-wide bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent">
              PLEXUS
            </h1>
            <span className="text-[10px] text-slate-500 font-mono tracking-widest">
              v0.1.0 (BETA)
            </span>
          </div>
        </div>

        {/* Menu Items */}
        <nav className="flex flex-col gap-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 text-left ${
                  isActive 
                    ? "bg-primary/10 text-primary border-l-2 border-primary" 
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-primary glow-primary" : ""}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* System Status / Footer */}
      <div className="glass-panel rounded-xl p-4 flex flex-col gap-3">
        <div className="flex items-center gap-2 justify-between">
          <span className="text-xs text-slate-500 font-mono">AGENT RUNNER</span>
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
        </div>
        <div className="text-[11px] text-slate-400 font-mono leading-relaxed">
          SPECTRA Engine: <span className="text-primary">ACTIVE</span>
        </div>
      </div>
    </aside>
  );
}
