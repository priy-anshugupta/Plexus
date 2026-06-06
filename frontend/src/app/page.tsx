"use client";

import React, { useState } from "react";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";
import { useRole } from "../context/RoleContext";
import { defineAbilityFor } from "../lib/ability";

// Import dashboards
import CisoDashboard from "../components/dashboards/CisoDashboard";
import CtoDashboard from "../components/dashboards/CtoDashboard";
import QuestDashboard from "../components/dashboards/QuestDashboard";

// Import other icons for placeholders
import { 
  GitFork, 
  Plus, 
  SearchCode, 
  ShieldAlert, 
  ExternalLink,
  ChevronRight,
  Database,
  Sparkles,
  RefreshCcw,
  Binary
} from "lucide-react";
import BlastRadiusGraph from "../components/BlastRadiusGraph";

export default function MainPage() {
  const { role } = useRole();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [isScanning, setIsScanning] = useState(false);
  const [scanOutput, setScanOutput] = useState<string[]>([]);
  
  // Define CASL ability for active view
  const ability = defineAbilityFor(role);

  // Trigger scan simulation (SSE status updates mock)
  const triggerScan = () => {
    setIsScanning(true);
    setScanOutput(["[1/5] Ingesting repository diffs...", "[2/5] Building code AST property graphs..."]);
    
    setTimeout(() => {
      setScanOutput(prev => [...prev, "[3/5] Launching 6 parallel AI auditing agents..."]);
    }, 1500);

    setTimeout(() => {
      setScanOutput(prev => [...prev, "[4/5] Merging and cross-validating finding signatures...", "[5/5] Mapping findings onto Blast Radius tree..."]);
    }, 3500);

    setTimeout(() => {
      setScanOutput(prev => [...prev, "✓ Scan completed! 3 vulnerabilities flagged."]);
      setIsScanning(false);
    }, 5000);
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case "dashboard":
        if (ability.can("read", "CisoDashboard")) {
          return <CisoDashboard />;
        } else if (ability.can("read", "CtoDashboard")) {
          return <CtoDashboard />;
        } else if (ability.can("read", "QuestDashboard")) {
          return <QuestDashboard />;
        }
        return <QuestDashboard />;

      case "repos":
        return (
          <div className="flex flex-col gap-6 animate-in fade-in duration-200">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-slate-200">Connected Repositories</h3>
                <span className="text-xs text-slate-500 font-mono">Manage codebase ingestion streams</span>
              </div>
              <button className="flex items-center gap-1.5 px-4 py-2 bg-primary text-slate-950 rounded-lg text-xs font-semibold hover:bg-primary-hover transition-colors">
                <Plus className="w-4 h-4" />
                <span>Connect Repository</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="glass-panel rounded-xl p-5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-slate-900 border border-white/5 rounded-lg text-slate-400">
                    <GitFork className="w-5 h-5 text-slate-300" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-200">plexus-core</h4>
                    <span className="text-xs text-slate-500 font-mono">priy-anshugupta/Plexus (main)</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold border bg-emerald-500/10 border-emerald-500/20 text-emerald-400">
                    CONNECTED
                  </span>
                  <ExternalLink className="w-4 h-4 text-slate-500 hover:text-slate-300 cursor-pointer" />
                </div>
              </div>

              <div className="glass-panel rounded-xl p-5 flex items-center justify-between border-dashed border-slate-800 opacity-60">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-slate-900 border border-white/5 rounded-lg text-slate-400">
                    <GitFork className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-400">frontend-dashboard</h4>
                    <span className="text-xs text-slate-500 font-mono">Disconnected</span>
                  </div>
                </div>
                <button className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-white/5 rounded-lg text-xs text-slate-300">
                  Connect
                </button>
              </div>
            </div>
          </div>
        );

      case "scans":
        return (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-200">
            {/* Scans Control */}
            <div className="lg:col-span-1 glass-panel rounded-xl p-6 flex flex-col gap-4">
              <div>
                <h3 className="font-semibold text-slate-200">Trigger Audit Run</h3>
                <span className="text-xs text-slate-500">Scan codebase with LangGraph specialist agents</span>
              </div>
              <button 
                onClick={triggerScan}
                disabled={isScanning}
                className="w-full flex items-center justify-center gap-2 py-2.5 bg-primary disabled:bg-slate-800 text-slate-950 disabled:text-slate-500 rounded-lg text-sm font-semibold hover:bg-primary-hover transition-colors"
              >
                {isScanning ? (
                  <>
                    <RefreshCcw className="w-4 h-4 animate-spin" />
                    <span>Running Scan Pipeline...</span>
                  </>
                ) : (
                  <>
                    <SearchCode className="w-4 h-4" />
                    <span>Run Multi-Agent Scan</span>
                  </>
                )}
              </button>
              
              {/* Scan logs view */}
              <div className="bg-[#06080c] border border-white/5 rounded-lg p-4 font-mono text-xs text-slate-400 min-h-[200px] flex flex-col gap-1.5 overflow-y-auto">
                <div className="text-[10px] text-slate-500 font-bold border-b border-white/5 pb-1 uppercase">
                  Scanner Logs
                </div>
                {scanOutput.length === 0 && (
                  <span className="text-slate-600 italic">No scanner runs triggered.</span>
                )}
                {scanOutput.map((log, i) => (
                  <div key={i} className={log.startsWith("✓") ? "text-emerald-400 font-semibold" : ""}>{log}</div>
                ))}
              </div>
            </div>

            {/* Run History */}
            <div className="lg:col-span-2 glass-panel rounded-xl p-6 flex flex-col gap-4">
              <div>
                <h3 className="font-semibold text-slate-200">Scan Execution History</h3>
                <span className="text-xs text-slate-500">History of codebase analysis runs</span>
              </div>

              <div className="flex flex-col gap-2">
                {[
                  { id: "s1", date: "June 05, 16:45", type: "Full Scan", findings: 24, status: "COMPLETED" },
                  { id: "s2", date: "June 03, 10:12", type: "Incremental", findings: 6, status: "COMPLETED" },
                  { id: "s3", date: "May 28, 09:33", type: "Full Scan", findings: 0, status: "FAILED" }
                ].map((s) => (
                  <div key={s.id} className="flex items-center justify-between p-3.5 bg-slate-900/40 border border-white/5 rounded-lg text-xs font-mono">
                    <div className="flex items-center gap-3">
                      <Database className="w-4 h-4 text-slate-500" />
                      <div>
                        <div className="text-slate-300 font-semibold">{s.type}</div>
                        <div className="text-[10px] text-slate-500">{s.date}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div>Findings: <span className="text-primary font-bold">{s.findings}</span></div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                        s.status === "COMPLETED" ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" : "bg-rose-500/10 border-rose-500/20 text-rose-400"
                      }`}>
                        {s.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case "findings":
        return <CisoDashboard />; // reuse findings list from CISO view as it is the standard inventory view

      case "explorer":
        // Full page interactive Graph Explorer
        return (
          <div className="flex flex-col gap-4 animate-in fade-in duration-200">
            <div>
              <h3 className="font-semibold text-slate-200">Interactive AST Graph Explorer</h3>
              <span className="text-xs text-slate-500">Traverse imports, calls, and relationships in real-time</span>
            </div>
            
            <div className="h-[600px]">
              <BlastRadiusGraph
                nodes={[
                  { id: "n1", name: "main.py", type: "file" },
                  { id: "n2", name: "config.py", type: "file" },
                  { id: "n3", name: "security.py", type: "file" },
                  { id: "n4", name: "get_user()", type: "function" },
                  { id: "n5", name: "hash_password()", type: "function" },
                  { id: "n6", name: "UserRouter", type: "class" },
                  { id: "n7", name: "/api/v1/auth/login", type: "api" },
                  { id: "v1", name: "SQL Injection", type: "vulnerability" }
                ]}
                links={[
                  { source: "n1", target: "n2", type: "IMPORTS" },
                  { source: "n1", target: "n3", type: "IMPORTS" },
                  { source: "n7", target: "n4", type: "CALLS" },
                  { source: "n4", target: "n5", type: "CALLS" },
                  { source: "n4", target: "n6", type: "CONTAINS" },
                  { source: "v1", target: "n4", type: "AFFECTS" }
                ]}
                vulnerabilityNodeId="v1"
              />
            </div>
          </div>
        );

      default:
        return <div>Tab not found</div>;
    }
  };

  return (
    <div className="flex min-h-screen bg-background-dark">
      {/* Sidebar navigation */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      {/* Main workspace area */}
      <div className="flex-1 flex flex-col">
        {/* Topbar control panel */}
        <Topbar activeTab={activeTab} />
        
        {/* Render Tab Contents */}
        <main className="p-8 flex-1">
          {renderTabContent()}
        </main>
      </div>
    </div>
  );
}
