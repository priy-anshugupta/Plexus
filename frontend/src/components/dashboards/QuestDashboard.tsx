"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  Trophy, 
  Compass, 
  Map,
  CheckCircle2,
  Circle,
  Lock,
  ArrowRight,
  Award
} from "lucide-react";

interface Quest {
  id: string;
  title: string;
  description: string;
  difficulty: "EASY" | "MEDIUM" | "HARD";
  xp: number;
  status: "completed" | "active" | "locked";
  actionText?: string;
}

const mockQuests: Quest[] = [
  {
    id: "q1",
    title: "FastAPI Connection Verification",
    description: "Launch the local Docker containers, check the FastAPI health route, and verify that PostgreSQL, Neo4j, Qdrant, and Redis report online status.",
    difficulty: "EASY",
    xp: 100,
    status: "completed"
  },
  {
    id: "q2",
    title: "Graph Database Exploration",
    description: "Connect to the Neo4j container visual browser, and run a simple Cypher query to count all File nodes in the code property graph.",
    difficulty: "EASY",
    xp: 150,
    status: "completed"
  },
  {
    id: "q3",
    title: "Remediate SQL Injection in RepositoryRouter",
    description: "Inspect the raw execute SQL call inside `repositories.py` line 52. Rewrite it to use proper parameter binding variables in SQLAlchemy.",
    difficulty: "MEDIUM",
    xp: 300,
    status: "active",
    actionText: "Open Code Viewer"
  },
  {
    id: "q4",
    title: "Configure Custom Semgrep Pre-Filter Rules",
    description: "Create a custom YAML rule checking for missing authorization checks on router endpoints, and verify it correctly flags endpoints.",
    difficulty: "MEDIUM",
    xp: 250,
    status: "locked"
  },
  {
    id: "q5",
    title: "End-to-End Scanning Run",
    description: "Clone a target test repository, run a full Plexus multi-agent security scan, and verify findings exports are registered.",
    difficulty: "HARD",
    xp: 500,
    status: "locked"
  }
];

const questContainerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.08, delayChildren: 0.2 },
  },
};

const questCardVariants = {
  hidden: { y: 18, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.4, ease: "easeOut" as const },
  },
};

function AnimatedXP({ target }: { target: number }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (target === 0) return;
    const duration = 900;
    const steps = 30;
    const increment = target / steps;
    const interval = duration / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        setCount(target);
        clearInterval(timer);
      } else {
        setCount(Math.round(current));
      }
    }, interval);
    return () => clearInterval(timer);
  }, [target]);

  return <>{count}</>;
}

export default function QuestDashboard() {
  const [quests] = useState<Quest[]>(mockQuests);

  const getDifficultyColor = (diff: string) => {
    switch (diff) {
      case "EASY": return "text-emerald-400";
      case "MEDIUM": return "text-yellow-400";
      default: return "text-rose-400";
    }
  };

  const completedCount = quests.filter((q) => q.status === "completed").length;
  const totalXP = quests
    .filter((q) => q.status === "completed")
    .reduce((sum, q) => sum + q.xp, 0);
  const progressPct = (completedCount / quests.length) * 100;

  return (
    <motion.div
      className="flex flex-col gap-6 w-full"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      {/* Onboarding progress panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Progress Card */}
        <motion.div
          className="glass-panel rounded-xl p-5 flex items-center justify-between col-span-2"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" as const }}
        >
          <div className="flex flex-col gap-1">
            <span className="text-xs text-slate-500 font-mono">ONBOARDING QUEST JOURNEY</span>
            <h3 className="text-xl font-bold text-slate-200">
              Codebase Cadet <span className="text-primary font-mono">Lv. 2</span>
            </h3>
            <span className="text-xs text-slate-400 mt-2">
              {completedCount} / {quests.length} Quests Completed ({Math.round(progressPct)}%)
            </span>
            <div className="w-96 bg-white/5 rounded-full h-2 mt-2 overflow-hidden relative">
              <motion.div
                className="bg-primary h-full rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progressPct}%` }}
                transition={{ duration: 1, delay: 0.3, ease: "easeOut" as const }}
              />
              <motion.div
                className="absolute inset-0 bg-primary/20 rounded-full h-full"
                style={{ width: `${progressPct}%` }}
                animate={{ opacity: [0.4, 0.8, 0.4] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              />
            </div>
          </div>
          <motion.div
            className="bg-primary/5 p-4 rounded-xl border border-primary/20 flex flex-col items-center"
            initial={{ scale: 0.85, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.25, type: "spring", stiffness: 200 }}
          >
            <Trophy className="w-8 h-8 text-primary glow-primary mb-1" />
            <span className="text-xs text-slate-400">Total Score</span>
            <span className="text-lg font-bold text-slate-100 font-mono">
              <AnimatedXP target={totalXP} /> XP
            </span>
          </motion.div>
        </motion.div>

        {/* Achievement Panel */}
        <motion.div
          className="glass-panel rounded-xl p-5 flex flex-col gap-3"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" as const }}
        >
          <span className="text-xs text-slate-500 font-mono">UNLOCKED BADGES</span>
          <div className="flex gap-2.5">
            <motion.div
              className="bg-emerald-500/10 p-2 rounded-lg border border-emerald-500/20 text-emerald-400"
              title="API Inspector"
              whileHover={{ scale: 1.15, rotate: -5 }}
              transition={{ type: "spring", stiffness: 350, damping: 15 }}
            >
              <Compass className="w-5 h-5" />
            </motion.div>
            <motion.div
              className="bg-teal-500/10 p-2 rounded-lg border border-teal-500/20 text-teal-400"
              title="Graph Pioneer"
              whileHover={{ scale: 1.15, rotate: 5 }}
              transition={{ type: "spring", stiffness: 350, damping: 15 }}
            >
              <Map className="w-5 h-5" />
            </motion.div>
            <motion.div
              className="bg-slate-900 border border-white/5 p-2 rounded-lg text-slate-600"
              title="Vulnerability Slayer (Locked)"
              whileHover={{ scale: 1.05 }}
            >
              <Award className="w-5 h-5" />
            </motion.div>
          </div>
        </motion.div>
      </div>

      {/* Quest board */}
      <div className="flex flex-col gap-3">
        <motion.div
          className="text-xs text-slate-500 font-mono uppercase tracking-wider px-1"
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.35, delay: 0.15 }}
        >
          Active Sandbox Quests
        </motion.div>

        <motion.div
          className="flex flex-col gap-3"
          variants={questContainerVariants}
          initial="hidden"
          animate="visible"
        >
          {quests.map((quest) => (
            <motion.div
              key={quest.id}
              variants={questCardVariants}
              whileHover={
                quest.status !== "locked"
                  ? {
                      y: -3,
                      transition: { duration: 0.2, ease: "easeOut" as const },
                    }
                  : undefined
              }
              className={`p-5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all duration-300 ${
                quest.status === "completed" ? "bg-emerald-950/5 border-emerald-500/25 opacity-70 hover:border-emerald-500/40" :
                quest.status === "active" ? "bg-slate-900 border-primary shadow-lg shadow-primary/5 hover:shadow-primary/10 hover:border-primary/60" :
                "bg-panel-dark/25 border-white/5 opacity-40 select-none"
              }`}
            >
              <div className="flex items-start gap-4">
                {/* Status Icon */}
                <div className="mt-0.5">
                  {quest.status === "completed" ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  ) : quest.status === "active" ? (
                    <Circle className="w-5 h-5 text-primary animate-pulse" />
                  ) : (
                    <Lock className="w-5 h-5 text-slate-600" />
                  )}
                </div>

                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-3">
                    <h4 className="font-semibold text-slate-200">{quest.title}</h4>
                    <span className={`text-[10px] font-bold font-mono ${getDifficultyColor(quest.difficulty)}`}>
                      {quest.difficulty}
                    </span>
                    <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded font-mono">
                      +{quest.xp} XP
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 max-w-2xl leading-relaxed">
                    {quest.description}
                  </p>
                </div>
              </div>

              {/* Action Button */}
              <div>
                {quest.status === "active" && (
                  <motion.button
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-slate-950 rounded-lg text-xs font-semibold hover:bg-primary-hover transition-colors"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <span>{quest.actionText || "Start Quest"}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </motion.button>
                )}
                {quest.status === "locked" && (
                  <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono px-3 py-1.5">
                    <Lock className="w-3.5 h-3.5" />
                    <span>Locked</span>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </motion.div>
  );
}
