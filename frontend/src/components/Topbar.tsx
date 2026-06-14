"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRole, UserRole } from "../context/RoleContext";
import { motion, AnimatePresence } from "framer-motion";
import { 
  User, 
  Database, 
  ChevronDown,
  Command,
  Bell
} from "lucide-react";

interface TopbarProps {
  activeTab: string;
}

export default function Topbar({ activeTab }: TopbarProps) {
  const { role, setRole } = useRole();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [backendStatus, setBackendStatus] = useState<"connected" | "offline" | "checking">("checking");
  const dropdownRef = useRef<HTMLDivElement>(null);

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
      } catch {
        setBackendStatus("offline");
      }
    }
    checkHealth();
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    if (dropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [dropdownOpen]);

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
    <motion.header
      className="h-[72px] border-b border-white/8 bg-[#090a08]/82 backdrop-blur-xl sticky top-0 z-40 flex items-center justify-between px-7"
      initial={{ y: -16, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.45, ease: "easeOut" as const }}
    >
      {/* Route Title */}
      <div>
        <motion.h2
          className="font-display font-semibold text-lg text-[#f4f2e8] tracking-tight"
          key={activeTab}
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3, ease: "easeOut" as const }}
        >
          {getTabTitle()}
        </motion.h2>
        <span className="text-[10px] text-slate-500 font-mono tracking-wider uppercase">
          Operations / {activeTab}
        </span>
      </div>

      {/* Action / Selector Panel */}
      <div className="flex items-center gap-3">
        <button className="hidden lg:flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[.035] border border-white/8 text-[11px] text-slate-500 font-mono hover:bg-white/[.06] transition-colors duration-200">
          <Command className="w-3.5 h-3.5" /> Search <span className="text-slate-600">⌘ K</span>
        </button>
        {/* Backend Connection Status */}
        <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/[.035] border border-white/8 text-[10px] font-mono">
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
        <motion.button
          className="p-2.5 rounded-lg bg-white/[.035] border border-white/8 text-slate-400 hover:text-primary transition-colors duration-200"
          whileHover={{ scale: 1.08 }}
          whileTap={{ scale: 0.95 }}
        >
          <Bell className="w-3.5 h-3.5" />
        </motion.button>

        {/* Role Switcher Selector */}
        <div className="relative" ref={dropdownRef}>
          <motion.button 
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2.5 px-4 py-2 rounded-lg bg-primary text-[#11130e] border border-primary text-xs font-semibold hover:bg-primary-hover transition-all duration-200"
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
          >
            <User className="w-3.5 h-3.5" />
            <span>Role: {role.toUpperCase()}</span>
            <motion.span
              animate={{ rotate: dropdownOpen ? 180 : 0 }}
              transition={{ duration: 0.25, ease: "easeInOut" }}
            >
              <ChevronDown className="w-3.5 h-3.5" />
            </motion.span>
          </motion.button>

          <AnimatePresence>
            {dropdownOpen && (
              <motion.div
                className="absolute right-0 mt-2 w-64 glass-panel rounded-lg shadow-2xl p-1 z-50"
                initial={{ opacity: 0, scale: 0.92, y: -8 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.92, y: -8 }}
                transition={{ duration: 0.18, ease: "easeOut" as const }}
              >
                <div className="px-3 py-2 text-[10px] text-slate-500 font-mono border-b border-white/5 uppercase">
                  Select View Persona
                </div>
                <motion.button
                  onClick={() => handleRoleChange("ciso")}
                  className={`w-full text-left px-3 py-2.5 rounded text-xs font-medium flex flex-col gap-0.5 transition-colors ${
                    role === "ciso" ? "bg-primary/10 text-primary" : "text-slate-300 hover:bg-white/5"
                  }`}
                  whileHover={{ x: 2 }}
                  transition={{ duration: 0.15 }}
                >
                  <span>CISO Compliance Dashboard</span>
                  <span className="text-[10px] text-slate-500 font-normal">SOC2, Severity scoring, threat matrices</span>
                </motion.button>
                <motion.button
                  onClick={() => handleRoleChange("cto")}
                  className={`w-full text-left px-3 py-2.5 rounded text-xs font-medium flex flex-col gap-0.5 transition-colors ${
                    role === "cto" ? "bg-primary/10 text-primary" : "text-slate-300 hover:bg-white/5"
                  }`}
                  whileHover={{ x: 2 }}
                  transition={{ duration: 0.15 }}
                >
                  <span>CTO Technical Debt Dashboard</span>
                  <span className="text-[10px] text-slate-500 font-normal">Velocity, ROI modeling, Code Health score</span>
                </motion.button>
                <motion.button
                  onClick={() => handleRoleChange("junior_dev")}
                  className={`w-full text-left px-3 py-2.5 rounded text-xs font-medium flex flex-col gap-0.5 transition-colors ${
                    role === "junior_dev" ? "bg-primary/10 text-primary" : "text-slate-300 hover:bg-white/5"
                  }`}
                  whileHover={{ x: 2 }}
                  transition={{ duration: 0.15 }}
                >
                  <span>Junior Dev Onboarding</span>
                  <span className="text-[10px] text-slate-500 font-normal">Sandbox onboarding tasks & interactive quests</span>
                </motion.button>
                <motion.button
                  onClick={() => handleRoleChange("solo_dev" as UserRole)}
                  className={`w-full text-left px-3 py-2.5 rounded text-xs font-medium flex flex-col gap-0.5 transition-colors ${
                    role === ("solo_dev" as UserRole) ? "bg-primary/10 text-primary" : "text-slate-300 hover:bg-white/5"
                  }`}
                  whileHover={{ x: 2 }}
                  transition={{ duration: 0.15 }}
                >
                  <span>Solo Developer</span>
                  <span className="text-[10px] text-slate-500 font-normal">Personal scanning, code quality & dependency health</span>
                </motion.button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.header>
  );
}
