"use client";

import React, { useState } from "react";
import CodeViewer from "../CodeViewer";
import BlastRadiusGraph, { GraphNode, GraphLink } from "../BlastRadiusGraph";
import { 
  Shield, 
  AlertOctagon, 
  CheckCircle, 
  HelpCircle,
  FileCode,
  ArrowRight,
  TrendingDown,
  Lock,
  Layers,
  ChevronRight,
  X
} from "lucide-react";

interface FindingItem {
  id: string;
  title: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  category: string;
  filePath: string;
  line: number;
  confidence: number;
  description: string;
  codeSnippet: string;
  nodes: GraphNode[];
  links: GraphLink[];
}

// Mock findings with graph structure for CISO visualization
const mockFindings: FindingItem[] = [
  {
    id: "f1",
    title: "SQL Injection in User Search Query",
    severity: "CRITICAL",
    category: "OWASP A03:2021-Injection",
    filePath: "backend/app/routers/repositories.py",
    line: 52,
    confidence: 0.95,
    description: "User input directly concatenated into raw execute query without binding parameters. This allows arbitrary database command execution.",
    codeSnippet: `def search_repositories(query: str, db = Depends(get_db)):\n    # VULNERABLE: Direct string interpolation into SQL query\n    raw_query = f"SELECT * FROM repositories WHERE name LIKE '%{query}%'"\n    results = db.execute(raw_query).all()\n    return results`,
    nodes: [
      { id: "v1", name: "SQL Injection", type: "vulnerability" },
      { id: "e1", name: "/api/v1/repositories/search", type: "api" },
      { id: "func1", name: "search_repositories()", type: "function" },
      { id: "cls1", name: "RepositoryRouter", type: "class" },
      { id: "db1", name: "repositories_table", type: "class" },
    ],
    links: [
      { source: "v1", target: "func1", type: "AFFECTS" },
      { source: "e1", target: "func1", type: "CALLS" },
      { source: "func1", target: "db1", type: "CALLS" },
      { source: "func1", target: "cls1", type: "CONTAINS" },
    ]
  },
  {
    id: "f2",
    title: "Hardcoded AWS Authentication Secrets",
    severity: "HIGH",
    category: "OWASP A02:2021-Cryptographic Failures",
    filePath: "backend/app/core/config.py",
    line: 15,
    confidence: 0.88,
    description: "Hardcoded AWS Secret Access Key detected in configuration file settings object default value. Secrets should be loaded from environment.",
    codeSnippet: `class Settings(BaseSettings):\n    # VULNERABLE: Hardcoded credential values\n    aws_access_key_id: str = "AKIAIOSFODNN7EXAMPLE"\n    aws_secret_access_key: str = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"`,
    nodes: [
      { id: "v2", name: "Hardcoded Key", type: "vulnerability" },
      { id: "file1", name: "config.py", type: "file" },
      { id: "cls2", name: "Settings", type: "class" },
      { id: "func2", name: "get_s3_client()", type: "function" },
      { id: "e2", name: "/api/v1/scans/upload", type: "api" }
    ],
    links: [
      { source: "v2", target: "cls2", type: "AFFECTS" },
      { source: "cls2", target: "file1", type: "CONTAINS" },
      { source: "func2", target: "cls2", type: "CALLS" },
      { source: "e2", target: "func2", type: "CALLS" }
    ]
  },
  {
    id: "f3",
    title: "Broken Object Level Authorization (BOLA)",
    severity: "HIGH",
    category: "OWASP A01:2021-Broken Access Control",
    filePath: "backend/app/routers/scans.py",
    line: 88,
    confidence: 0.90,
    description: "User requests scan results without checking if they belong to their organization ID, leading to horizontal privilege escalation.",
    codeSnippet: `@router.get("/scans/{scan_id}")\ndef get_scan_details(scan_id: UUID, current_user = Depends(get_current_user), db = Depends(get_db)):\n    # BOLA: Fetches scan by ID directly without verifying user ownership\n    scan = db.query(Scan).filter(Scan.id == scan_id).first()\n    return scan`,
    nodes: [
      { id: "v3", name: "BOLA Vuln", type: "vulnerability" },
      { id: "e3", name: "/api/v1/scans/{scan_id}", type: "api" },
      { id: "func3", name: "get_scan_details()", type: "function" },
      { id: "db2", name: "scans_table", type: "class" }
    ],
    links: [
      { source: "v3", target: "func3", type: "AFFECTS" },
      { source: "e3", target: "func3", type: "CALLS" },
      { source: "func3", target: "db2", type: "CALLS" }
    ]
  }
];

export default function CisoDashboard() {
  const [selectedFinding, setSelectedFinding] = useState<FindingItem | null>(null);

  const getSeverityStyles = (sev: string) => {
    switch (sev) {
      case "CRITICAL":
        return "bg-rose-500/10 border-rose-500/20 text-rose-400";
      case "HIGH":
        return "bg-orange-500/10 border-orange-500/20 text-orange-400";
      case "MEDIUM":
        return "bg-yellow-500/10 border-yellow-500/20 text-yellow-400";
      default:
        return "bg-blue-500/10 border-blue-500/20 text-blue-400";
    }
  };

  return (
    <div className="flex flex-col gap-6 w-full">
      {/* Overview Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Compliance Card */}
        <div className="glass-panel rounded-xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono">SOC2 COMPLIANCE</span>
            <Lock className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-display font-bold text-emerald-400 glow-primary">88%</span>
            <span className="text-xs text-slate-500">Ready</span>
          </div>
          <div className="mt-2 w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
            <div className="bg-emerald-400 h-full" style={{ width: "88%" }} />
          </div>
        </div>

        {/* ISO 27001 Card */}
        <div className="glass-panel rounded-xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono">ISO 27001 POSTURE</span>
            <Layers className="w-4 h-4 text-teal-400" />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-display font-bold text-teal-400">74%</span>
            <span className="text-xs text-slate-500">Compliant</span>
          </div>
          <div className="mt-2 w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
            <div className="bg-teal-400 h-full" style={{ width: "74%" }} />
          </div>
        </div>

        {/* Critical Dials */}
        <div className="glass-panel rounded-xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono">CRITICAL THREATS</span>
            <AlertOctagon className="w-4 h-4 text-rose-500" />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-display font-bold text-rose-500 glow-accent">2</span>
            <span className="text-xs text-slate-500">Unresolved</span>
          </div>
          <div className="text-[10px] text-slate-500 font-mono mt-2 flex items-center gap-1">
            <TrendingDown className="w-3.5 h-3.5 text-emerald-400" />
            <span>Down 50% from last scan</span>
          </div>
        </div>

        {/* Unified Score */}
        <div className="glass-panel rounded-xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono">SECURITY POSTURE SCORE</span>
            <Shield className="w-4 h-4 text-primary" />
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-display font-bold text-primary">82.4</span>
            <span className="text-xs text-slate-500">/ 100</span>
          </div>
          <div className="text-[10px] text-slate-500 font-mono mt-2">
            Grade: <span className="text-primary font-bold">EXCELLENT</span>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Vulnerability Inventory List */}
        <div className="lg:col-span-1 flex flex-col gap-3">
          <div className="text-xs text-slate-500 font-mono uppercase tracking-wider px-1">
            Vulnerability Inventory
          </div>
          
          <div className="flex flex-col gap-2">
            {mockFindings.map((finding) => (
              <button
                key={finding.id}
                onClick={() => setSelectedFinding(finding)}
                className={`w-full text-left p-4 rounded-xl border transition-all duration-300 relative overflow-hidden ${
                  selectedFinding?.id === finding.id 
                    ? "bg-slate-900 border-primary shadow-lg" 
                    : "bg-panel-dark/25 hover:bg-slate-900/40 border-white/5"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getSeverityStyles(finding.severity)}`}>
                    {finding.severity}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">
                    Conf: {Math.round(finding.confidence * 100)}%
                  </span>
                </div>
                <h4 className="text-sm font-semibold text-slate-200 line-clamp-1 mb-1">
                  {finding.title}
                </h4>
                <div className="text-[11px] text-slate-500 font-mono truncate mb-2">
                  {finding.filePath}
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 mt-2 pt-2 border-t border-white/5">
                  <span className="truncate max-w-[200px] text-slate-500">{finding.category}</span>
                  <ChevronRight className="w-4 h-4 text-slate-600" />
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Detailed Inspection Split Screen */}
        <div className="lg:col-span-2">
          {selectedFinding ? (
            <div className="flex flex-col gap-4 animate-in fade-in duration-300">
              {/* Header Info */}
              <div className="glass-panel rounded-xl p-5 relative">
                <button
                  onClick={() => setSelectedFinding(null)}
                  className="absolute top-4 right-4 text-slate-500 hover:text-slate-200"
                >
                  <X className="w-4 h-4" />
                </button>
                <div className="flex items-center gap-3 mb-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getSeverityStyles(selectedFinding.severity)}`}>
                    {selectedFinding.severity}
                  </span>
                  <span className="text-xs text-slate-500 font-mono">{selectedFinding.category}</span>
                </div>
                <h3 className="text-lg font-bold text-slate-100 mb-2">
                  {selectedFinding.title}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  {selectedFinding.description}
                </p>
                <div className="flex gap-4 text-xs font-mono text-slate-500 border-t border-white/5 pt-3">
                  <div>File: <span className="text-slate-300">{selectedFinding.filePath}</span></div>
                  <div>Line: <span className="text-slate-300">{selectedFinding.line}</span></div>
                </div>
              </div>

              {/* Code Snippet and Blast Radius Tabs */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex flex-col gap-2">
                  <div className="text-xs text-slate-500 font-mono uppercase tracking-wider px-1">
                    AST Code Context
                  </div>
                  <div className="h-[350px]">
                    <CodeViewer
                      code={selectedFinding.codeSnippet}
                      filePath={selectedFinding.filePath}
                      highlightLine={selectedFinding.line}
                    />
                  </div>
                </div>

                <div className="flex flex-col gap-2">
                  <div className="text-xs text-slate-500 font-mono uppercase tracking-wider px-1">
                    Graph Blast Radius Visualization
                  </div>
                  <div className="h-[350px]">
                    <BlastRadiusGraph
                      nodes={selectedFinding.nodes}
                      links={selectedFinding.links}
                      vulnerabilityNodeId="v1"
                    />
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-panel rounded-xl p-8 flex flex-col items-center justify-center text-center h-[500px] border-dashed border-slate-800">
              <Shield className="w-12 h-12 text-slate-700 animate-pulse mb-4" />
              <h3 className="text-slate-400 font-semibold mb-2">No Vulnerability Selected</h3>
              <p className="text-xs text-slate-500 max-w-sm">
                Click on any vulnerability in the inventory list to view its code context and calculate its downstream impact.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
