"use client";

import React, { useState } from "react";
import { 
  Trophy, 
  BookOpen, 
  Compass, 
  Map,
  CheckCircle2,
  Circle,
  Play,
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

export default function QuestDashboard() {
  const [quests, setQuests] = useState<Quest[]>(mockQuests);

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

  return (
    <div className="flex flex-col gap-6 w-full">
      {/* Onboarding progress panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Progress Card */}
        <div className="glass-panel rounded-xl p-5 flex items-center justify-between col-span-2">
          <div className="flex flex-col gap-1">
            <span className="text-xs text-slate-500 font-mono">ONBOARDING QUEST JOURNEY</span>
            <h3 className="text-xl font-bold text-slate-200">
              Codebase Cadet <span className="text-primary font-mono">Lv. 2</span>
            </h3>
            <span className="text-xs text-slate-400 mt-2">
              {completedCount} / {quests.length} Quests Completed ({Math.round((completedCount / quests.length) * 100)}%)
            </span>
            <div className="w-96 bg-white/5 rounded-full h-2 mt-2 overflow-hidden">
              <div className="bg-primary h-full" style={{ width: `${(completedCount / quests.length) * 100}%` }} />
            </div>
          </div>
          <div className="bg-primary/5 p-4 rounded-xl border border-primary/20 flex flex-col items-center">
            <Trophy className="w-8 h-8 text-primary glow-primary mb-1" />
            <span className="text-xs text-slate-400">Total Score</span>
            <span className="text-lg font-bold text-slate-100 font-mono">{totalXP} XP</span>
          </div>
        </div>

        {/* Achievement Panel */}
        <div className="glass-panel rounded-xl p-5 flex flex-col gap-3">
          <span className="text-xs text-slate-500 font-mono">UNLOCKED BADGES</span>
          <div className="flex gap-2.5">
            <div className="bg-emerald-500/10 p-2 rounded-lg border border-emerald-500/20 text-emerald-400" title="API Inspector">
              <Compass className="w-5 h-5" />
            </div>
            <div className="bg-teal-500/10 p-2 rounded-lg border border-teal-500/20 text-teal-400" title="Graph Pioneer">
              <Map className="w-5 h-5" />
            </div>
            <div className="bg-slate-900 border border-white/5 p-2 rounded-lg text-slate-600" title="Vulnerability Slayer (Locked)">
              <Award className="w-5 h-5" />
            </div>
          </div>
        </div>
      </div>

      {/* Quest board */}
      <div className="flex flex-col gap-3">
        <div className="text-xs text-slate-500 font-mono uppercase tracking-wider px-1">
          Active Sandbox Quests
        </div>

        <div className="flex flex-col gap-3">
          {quests.map((quest) => (
            <div
              key={quest.id}
              className={`p-5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all duration-300 ${
                quest.status === "completed" ? "bg-emerald-950/5 border-emerald-500/25 opacity-70" :
                quest.status === "active" ? "bg-slate-900 border-primary shadow-lg shadow-primary/5" :
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
                  <button className="flex items-center gap-2 px-4 py-2 bg-primary text-slate-950 rounded-lg text-xs font-semibold hover:bg-primary-hover transition-colors">
                    <span>{quest.actionText || "Start Quest"}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                )}
                {quest.status === "locked" && (
                  <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono px-3 py-1.5">
                    <Lock className="w-3.5 h-3.5" />
                    <span>Locked</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
