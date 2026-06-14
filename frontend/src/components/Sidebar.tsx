"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { 
  LayoutDashboard, 
  GitFork, 
  SearchCode, 
  ShieldAlert, 
  Binary,
  Network,
  Radio,
  TerminalSquare,
  LogOut
} from "lucide-react";

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const sidebarVariants = {
  hidden: { x: -20, opacity: 0 },
  visible: {
    x: 0,
    opacity: 1,
    transition: { duration: 0.5, ease: "easeOut" as const },
  },
};

const navVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.05, delayChildren: 0.15 },
  },
};

const itemVariants = {
  hidden: { x: -16, opacity: 0 },
  visible: {
    x: 0,
    opacity: 1,
    transition: { duration: 0.35, ease: "easeOut" as const },
  },
};

export default function Sidebar({ activeTab, setActiveTab }: SidebarProps) {
  const menuItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "repos", label: "Repositories", icon: GitFork },
    { id: "scans", label: "Scans", icon: SearchCode },
    { id: "findings", label: "Findings", icon: ShieldAlert },
    { id: "explorer", label: "Code Explorer", icon: Binary },
  ];

  return (
    <motion.aside
      className="w-[232px] bg-[#0c0e0a]/95 border-r border-white/8 flex flex-col justify-between p-3 min-h-screen sticky top-0 z-50"
      variants={sidebarVariants}
      initial="hidden"
      animate="visible"
    >
      <div className="flex flex-col gap-8">
        {/* Brand Logo */}
        <motion.div
          className="flex items-center gap-3 px-2 py-4"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" as const }}
        >
          <div className="bg-primary text-[#10120d] p-2 rounded-lg shadow-[0_0_24px_rgba(199,243,107,.18)]">
            <Network className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-display font-bold text-lg tracking-[0.18em] text-[#f4f2e8]">
              PLEXUS<span className="text-primary">.</span>
            </h1>
            <span className="text-[9px] text-slate-500 font-mono tracking-[0.16em]">
              CODE INTELLIGENCE
            </span>
          </div>
        </motion.div>

        {/* Menu Items */}
        <motion.nav
          className="flex flex-col gap-1"
          variants={navVariants}
          initial="hidden"
          animate="visible"
        >
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <motion.button
                key={item.id}
                variants={itemVariants}
                onClick={() => setActiveTab(item.id)}
                whileHover={{ x: 4 }}
                whileTap={{ scale: 0.97 }}
                animate={isActive ? { scale: 1.02 } : { scale: 1 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 text-left ${
                  isActive 
                    ? "bg-primary text-[#11130e] shadow-[0_8px_24px_rgba(199,243,107,.12)]"
                    : "text-slate-400 hover:bg-white/5 hover:text-[#f4f2e8]"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </motion.button>
            );
          })}
        </motion.nav>
      </div>

      <div className="flex flex-col gap-3">
        {/* System Status / Footer */}
        <motion.div
          className="rounded-xl p-4 flex flex-col gap-3 bg-[#14170f] border border-white/8"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4, ease: "easeOut" as const }}
        >
          <div className="flex items-center gap-2 justify-between">
            <span className="text-[10px] text-slate-500 font-mono tracking-wider">AGENT MESH</span>
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
            <div className="rounded-md bg-black/20 p-2 text-slate-500"><Radio className="w-3 h-3 mb-1 text-primary" />6 ONLINE</div>
            <div className="rounded-md bg-black/20 p-2 text-slate-500"><TerminalSquare className="w-3 h-3 mb-1 text-secondary" />42ms</div>
          </div>
        </motion.div>

        {/* Sign Out Link */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.55 }}
        >
          <Link
            href="/"
            className="flex items-center gap-2.5 px-4 py-2.5 rounded-lg text-xs font-medium text-slate-500 hover:text-slate-300 hover:bg-white/5 transition-all duration-200 group"
          >
            <LogOut className="w-3.5 h-3.5 group-hover:translate-x-[-2px] transition-transform duration-200" />
            <span>Sign Out</span>
          </Link>
        </motion.div>
      </div>
    </motion.aside>
  );
}
