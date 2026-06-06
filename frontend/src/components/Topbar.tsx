"use client";

import React, { useState, useEffect } from "react";
import { useRole, UserRole } from "../context/RoleContext";
import { 
  User, 
  Database, 
  Cpu, 
  CircleDot,
  ChevronDown
} from "lucide-react";

interface TopbarProps {
  activeTab: string;
}

export default function Topbar({ activeTab }: TopbarProps) {
  const { role, setRole, roleName } = useRole();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [backendStatus, setBackendStatus] = useState<"connected" | "offline" | "checking">("checking");

  useEffect(() => {
    // Check backend health
    async function checkHealth() {
      try {
        const res = await fetch("http://localhost:8000/health");
        if (res.ok) {
          setBackendStatus("connected");
        } else {
          setBackendStatus("offline");
        }
      } catch (err) {
        setBackendStatus("offline");
      }
    }
    checkHealth();
  }, []);

  const getTabTitle = () => {
    switch (activeTab) {
      case "dashboard": return "Security & DevEx Posture";
      case "repos": return "Repository Inventory";
      case "scans": return "AI Agent Scans";
      case "findings": return "Vulnerability Inventory";
      case "explorer": return "Interactive Graph Code Explorer";
      default: return "Plexus Platform";
    }
  };

  const handleRoleChange = (newRole: UserRole) => {
    setRole(newRole);
    setDropdownOpen(false);
  };

  return (
    <header className="h-16 border-b border-white/5 bg-background-dark/30 backdrop-blur-md sticky top-0 z-40 flex items-center justify-between px-8">
      {/* Route Title */}
      <div>
        <h2 className="font-display font-semibold text-lg text-slate-100">
          {getTabTitle()}
        </h2>
        <span className="text-[11px] text-slate-400 font-mono">
          Plexus Platform / {activeTab}
        </span>
      </div>

      {/* Action / Selector Panel */}
      <div className="flex items-center gap-6">
        {/* Backend Connection Status */}
        <div className="flex items-center gap-3 px-3 py-1.5 rounded-lg bg-white/5 border border-white/5 text-xs font-mono">
          <div className="flex items-center gap-1.5 text-slate-400">
            <Database className="w-3.5 h-3.5" />
            <span>API Server:</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className={`h-1.5 w-1.5 rounded-full ${
              backendStatus === "connected" ? "bg-emerald-400 animate-pulse" : 
              backendStatus === "offline" ? "bg-rose-500" : "bg-yellow-500"
            }`} />
            <span className={backendStatus === "connected" ? "text-emerald-400" : backendStatus === "offline" ? "text-rose-500" : "text-yellow-500"}>
              {backendStatus.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Role Switcher Selector */}
        <div className="relative">
          <button 
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2.5 px-4 py-2 rounded-lg bg-primary/10 border border-primary/20 text-xs font-medium text-primary hover:bg-primary/15 transition-all duration-200"
          >
            <User className="w-3.5 h-3.5 text-primary" />
            <span>Role: {role.toUpperCase()}</span>
            <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${dropdownOpen ? "rotate-180" : ""}`} />
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-64 glass-panel rounded-lg shadow-2xl p-1 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
              <div className="px-3 py-2 text-[10px] text-slate-500 font-mono border-b border-white/5 uppercase">
                Select View Persona
              </div>
              <button 
                onClick={() => handleRoleChange("ciso")}
                className={`w-full text-left px-3 py-2.5 rounded text-xs font-medium flex flex-col gap-0.5 transition-colors ${
                  role === "ciso" ? "bg-primary/10 text-primary" : "text-slate-300 hover:bg-white/5"
                }`}
              >
                <span>CISO Compliance Dashboard</span>
                <span className="text-[10px] text-slate-500 font-normal">SOC2, Severity scoring, threat matrices</span>
              </button>
              <button 
                onClick={() => handleRoleChange("cto")}
                className={`w-full text-left px-3 py-2.5 rounded text-xs font-medium flex flex-col gap-0.5 transition-colors ${
                  role === "cto" ? "bg-primary/10 text-primary" : "text-slate-300 hover:bg-white/5"
                }`}
              >
                <span>CTO Technical Debt Dashboard</span>
                <span className="text-[10px] text-slate-500 font-normal">Velocity, ROI modeling, Code Health score</span>
              </button>
              <button 
                onClick={() => handleRoleChange("junior_dev")}
                className={`w-full text-left px-3 py-2.5 rounded text-xs font-medium flex flex-col gap-0.5 transition-colors ${
                  role === "junior_dev" ? "bg-primary/10 text-primary" : "text-slate-300 hover:bg-white/5"
                }`}
              >
                <span>Junior Dev Onboarding</span>
                <span className="text-[10px] text-slate-500 font-normal">Sandbox onboarding tasks & interactive quests</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
