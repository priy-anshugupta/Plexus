"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  KeyRound,
  Package,
  Star,
  Bug,
  ChevronRight,
  Play,
  FileBarChart,
  List,
  GitFork,
  Plus,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  Info,
  GitBranch,
  Upload,
  X,
  Loader2,
} from "lucide-react";
import type { Finding } from "../../lib/api";

/* Animation */
const staggerContainer = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.09, delayChildren: 0.1 } },
};
const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } },
};

interface SoloDashboardProps {
  findings?: Finding[];
  onScan?: () => void;
  isScanning?: boolean;
}

function getSeverityStyles(sev: string) {
  switch (sev.toUpperCase()) {
    case "CRITICAL":
    case "HIGH":
      return { badge: "bg-orange-500/10 border-orange-500/20 text-orange-400", icon: AlertTriangle, iconClass: "text-orange-400" };
    case "MEDIUM":
      return { badge: "bg-yellow-500/10 border-yellow-500/20 text-yellow-400", icon: AlertTriangle, iconClass: "text-yellow-400" };
    default:
      return { badge: "bg-blue-500/10 border-blue-500/20 text-blue-400", icon: Info, iconClass: "text-blue-400" };
  }
}

export default function SoloDashboard({ findings = [], onScan, isScanning = false }: SoloDashboardProps) {
  const [selectedFinding, setSelectedFinding] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [repoUrl, setRepoUrl] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [repos, setRepos] = useState([
    { id: "r1", name: "my-project", url: "github.com/user/my-project" },
  ]);

  const handleAddRepo = (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl) return;
    setIsConnecting(true);
    setTimeout(() => {
      const name = repoUrl.split("/").pop() || "new-repo";
      setRepos([...repos, { id: Date.now().toString(), name, url: repoUrl }]);
      setIsConnecting(false);
      setIsModalOpen(false);
      setRepoUrl("");
    }, 1500);
  };

  // Compute stats from real findings
  const secrets = findings.filter((f) => f.rule_id?.includes("SECRET")).length;
  const vulns = findings.filter((f) => f.category === "security").length;
  const quality = findings.filter((f) => f.category === "code_quality").length;
  const critical = findings.filter((f) => f.severity === "critical").length;

  const statCards = [
    { label: "SECRETS DETECTED", value: secrets.toString(), status: secrets === 0 ? "Clean" : `${secrets} found`, statusColor: secrets === 0 ? "text-emerald-400" : "text-amber-400", icon: KeyRound, iconColor: secrets === 0 ? "text-emerald-400" : "text-amber-400" },
    { label: "DEPENDENCY HEALTH", value: "95%", status: "3 outdated", statusColor: "text-amber-400", icon: Package, iconColor: "text-amber-400" },
    { label: "CODE QUALITY", value: quality > 0 ? "B+" : "A-", status: quality > 0 ? `${quality} issues` : "Above average", statusColor: "text-primary", icon: Star, iconColor: "text-primary" },
    { label: "VULNERABILITIES", value: vulns.toString(), status: critical > 0 ? `${critical} critical` : "2 fixed since last scan", statusColor: critical > 0 ? "text-rose-400" : "text-emerald-400", icon: Bug, iconColor: critical > 0 ? "text-rose-400" : "text-emerald-400" },
  ];

  return (
    <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="flex flex-col gap-6 w-full">
      {/* Bento Stat Cards */}
      <motion.div variants={staggerContainer} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <motion.div key={card.label} variants={fadeUp} className="bento-card">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[10px] font-mono tracking-wider">{card.label}</span>
                <Icon className={`w-4 h-4 ${card.iconColor}`} />
              </div>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-3xl font-display font-bold text-[#f4f2e8] glow-primary">{card.value}</span>
              </div>
              <div className={`text-[10px] font-mono mt-2 flex items-center gap-1 ${card.statusColor}`}>
                <CheckCircle2 className="w-3 h-3" />
                <span>{card.status}</span>
              </div>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Recent Scan Results */}
      <motion.div variants={fadeUp} className="flex flex-col gap-3">
        <div className="text-xs text-slate-500 font-mono uppercase tracking-wider px-1">Recent Findings</div>
        <div className="flex flex-col gap-2">
          {findings.length === 0 && (
            <div className="text-slate-500 text-sm py-4">No findings yet. Run a scan to see results.</div>
          )}
          {findings.map((finding) => {
            const sevInfo = getSeverityStyles(finding.severity);
            const SevIcon = sevInfo.icon;
            const isSelected = selectedFinding === finding.id;
            return (
              <motion.button
                key={finding.id}
                variants={fadeUp}
                onClick={() => setSelectedFinding(isSelected ? null : finding.id)}
                className={`w-full text-left p-4 rounded-xl border transition-all duration-300 relative overflow-hidden ${
                  isSelected ? "bg-slate-900 border-primary/40 shadow-lg" : "bg-panel-dark/25 hover:bg-slate-900/40 border-white/5"
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className={`p-2 rounded-lg bg-white/[0.03] border border-white/5 ${sevInfo.iconClass}`}>
                    <SevIcon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="text-sm font-semibold text-slate-200 truncate">{finding.title}</h4>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border shrink-0 ${sevInfo.badge}`}>
                        {finding.severity}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono">
                      <span>{finding.file_path}:{finding.line_start}</span>
                      <span className="text-slate-600">•</span>
                      <span className="text-slate-400 truncate">{finding.description}</span>
                    </div>
                    {isSelected && (
                      <div className="mt-3 p-3 rounded-lg bg-black/30 border border-white/5 text-xs text-slate-300 leading-relaxed">
                        <div className="font-semibold text-primary mb-1">Suggestion</div>
                        <div className="whitespace-pre-wrap">{finding.suggestion}</div>
                        {finding.code_snippet && (
                          <pre className="mt-2 p-2 bg-black/40 rounded text-[10px] font-mono text-slate-400 overflow-x-auto">
                            {finding.code_snippet}
                          </pre>
                        )}
                      </div>
                    )}
                  </div>
                  <ChevronRight className={`w-4 h-4 text-slate-600 shrink-0 transition-transform duration-200 ${isSelected ? "rotate-90 text-primary" : ""}`} />
                </div>
              </motion.button>
            );
          })}
        </div>
      </motion.div>

      {/* Quick Actions */}
      <motion.div variants={fadeUp} className="flex flex-col gap-3">
        <div className="text-xs text-slate-500 font-mono uppercase tracking-wider px-1">Quick Actions</div>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={onScan}
            disabled={isScanning}
            className="flex items-center gap-2 px-5 py-2.5 bg-primary text-[#11130e] rounded-xl text-sm font-semibold hover:bg-primary-hover transition-colors shadow-[0_8px_24px_rgba(199,243,107,.12)] disabled:opacity-50"
          >
            {isScanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {isScanning ? "Scanning..." : "Scan Now"}
          </button>
          <button className="flex items-center gap-2 px-5 py-2.5 bg-white/[0.04] border border-white/8 text-slate-300 rounded-xl text-sm font-medium hover:bg-white/[0.07] hover:border-white/15 transition-all">
            <List className="w-4 h-4" />
            View Dependencies
          </button>
          <button className="flex items-center gap-2 px-5 py-2.5 bg-white/[0.04] border border-white/8 text-slate-300 rounded-xl text-sm font-medium hover:bg-white/[0.07] hover:border-white/15 transition-all">
            <FileBarChart className="w-4 h-4" />
            Export Report
          </button>
        </div>
      </motion.div>

      {/* Connected Repositories */}
      <motion.div variants={fadeUp} className="flex flex-col gap-3">
        <div className="text-xs text-slate-500 font-mono uppercase tracking-wider px-1">Connected Repositories</div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {repos.map((repo) => (
            <div key={repo.id} className="glass-panel rounded-xl p-5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-slate-900 border border-white/5 rounded-lg text-slate-400">
                  <GitFork className="w-5 h-5 text-slate-300" />
                </div>
                <div>
                  <h4 className="font-semibold text-slate-200">{repo.name}</h4>
                  <span className="text-xs text-slate-500 font-mono">{repo.url} (main)</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold border bg-emerald-500/10 border-emerald-500/20 text-emerald-400">CONNECTED</span>
                <ExternalLink className="w-4 h-4 text-slate-500 hover:text-slate-300 cursor-pointer" />
              </div>
            </div>
          ))}
          <div
            onClick={() => setIsModalOpen(true)}
            className="glass-panel rounded-xl p-5 flex items-center justify-center border-dashed border-slate-800 opacity-60 hover:opacity-100 transition-opacity cursor-pointer group"
          >
            <div className="flex items-center gap-3 text-slate-500 group-hover:text-primary transition-colors">
              <Plus className="w-5 h-5" />
              <span className="text-sm font-medium">Add repository</span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Add Repository Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              className="bg-[#0c0e0a] border border-white/10 rounded-2xl p-6 w-full max-w-lg shadow-2xl relative overflow-hidden"
            >
              <button onClick={() => setIsModalOpen(false)} className="absolute top-4 right-4 text-slate-500 hover:text-slate-300 transition-colors">
                <X className="w-5 h-5" />
              </button>
              <h3 className="text-xl font-semibold text-slate-200 mb-2">Add Repository</h3>
              <p className="text-sm text-slate-400 mb-6">Connect a remote repository or upload a local folder to begin scanning.</p>
              <form onSubmit={handleAddRepo} className="flex flex-col gap-6">
                <div className="grid grid-cols-2 gap-4">
                  <button type="button" className="flex flex-col items-center gap-3 p-4 rounded-xl border border-primary/40 bg-primary/5 text-primary transition-colors">
                    <GitBranch className="w-6 h-6" />
                    <span className="text-sm font-medium">Git URL</span>
                  </button>
                  <button type="button" className="flex flex-col items-center gap-3 p-4 rounded-xl border border-white/5 bg-white/[0.02] text-slate-400 hover:border-white/20 hover:text-slate-300 transition-colors">
                    <Upload className="w-6 h-6" />
                    <span className="text-sm font-medium">Local Folder</span>
                  </button>
                </div>
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Repository URL</label>
                  <input
                    type="text"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    placeholder="https://github.com/user/repo"
                    className="w-full bg-[#14170f] border border-white/10 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={isConnecting || !repoUrl}
                  className="w-full flex items-center justify-center gap-2 px-5 py-3 bg-primary text-[#11130e] rounded-xl font-semibold hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {isConnecting ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Connecting...
                    </>
                  ) : (
                    "Connect Repository"
                  )}
                </button>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
