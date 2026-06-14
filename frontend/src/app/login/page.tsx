"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { motion, Variants } from "framer-motion";
import { useRole } from "../../context/RoleContext";
import {
  Code2,
  Building2,
  ArrowLeft,
  Check,
  Network,
} from "lucide-react";

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.18, delayChildren: 0.3 },
  },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 32 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: "easeOut" as const },
  },
};

const cardVariants: Variants = {
  hidden: { opacity: 0, y: 48, scale: 0.96 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.7, ease: "easeOut" as const },
  },
};

interface FeatureItemProps {
  text: string;
}

function FeatureItem({ text }: FeatureItemProps) {
  return (
    <li className="flex items-center gap-2.5 text-sm text-slate-400">
      <Check className="w-3.5 h-3.5 text-primary shrink-0" />
      <span>{text}</span>
    </li>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const { setRole } = useRole();

  const handleSoloDev = () => {
    setRole("solo_dev");
    router.push("/dashboard");
  };

  const handleEnterprise = () => {
    setRole("ciso");
    router.push("/dashboard");
  };

  return (
    <div className="relative min-h-screen bg-[#0c0c0c] flex flex-col items-center justify-center overflow-hidden">
      {/* Ambient background gradients */}
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute top-[-20%] left-[15%] w-[600px] h-[600px] rounded-full bg-primary/[0.06] blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[10%] w-[500px] h-[500px] rounded-full bg-accent/[0.04] blur-[100px]" />
        <div className="absolute top-[40%] right-[30%] w-[350px] h-[350px] rounded-full bg-info/[0.03] blur-[90px]" />
      </div>

      {/* Subtle grid overlay */}
      <div
        className="pointer-events-none fixed inset-0 z-0 opacity-[0.12]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.03) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
          maskImage: "linear-gradient(to bottom, black 30%, transparent 80%)",
          WebkitMaskImage:
            "linear-gradient(to bottom, black 30%, transparent 80%)",
        }}
      />

      {/* Back to Home link */}
      <motion.div
        initial={{ opacity: 0, x: -16 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="fixed top-6 left-6 z-50"
      >
        <button
          onClick={() => router.push("/")}
          className="flex items-center gap-2 text-xs text-slate-500 hover:text-primary transition-colors font-mono group"
        >
          <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
          Back to home
        </button>
      </motion.div>

      {/* Main Content */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="relative z-10 flex flex-col items-center w-full max-w-5xl px-6 py-12"
      >
        {/* Logo */}
        <motion.div
          variants={itemVariants}
          className="flex items-center gap-3 mb-10"
        >
          <div className="bg-primary text-[#10120d] p-2.5 rounded-xl shadow-[0_0_32px_rgba(199,243,107,.2)]">
            <Network className="w-6 h-6" />
          </div>
          <h1 className="font-display font-bold text-2xl tracking-[0.18em] text-[#f4f2e8]">
            PLEXUS<span className="text-primary">.</span>
          </h1>
        </motion.div>

        {/* Headline */}
        <motion.div variants={itemVariants} className="text-center mb-12">
          <h2 className="font-display text-4xl md:text-5xl font-bold tracking-tight text-[#f4f2e8] mb-4">
            Welcome to Plexus
          </h2>
          <p className="text-slate-500 text-base md:text-lg max-w-lg mx-auto">
            Choose how you want to explore
          </p>
        </motion.div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl">
          {/* Card 1 — Solo Developer */}
          <motion.div
            variants={cardVariants}
            whileHover={{
              scale: 1.02,
              boxShadow: "0 0 48px rgba(199, 243, 107, 0.12)",
            }}
            className="group relative rounded-2xl border border-white/[0.08] bg-gradient-to-b from-[#181b14]/95 to-[#0e100c]/95 backdrop-blur-xl p-8 flex flex-col cursor-pointer transition-all duration-300 hover:border-primary/30 overflow-hidden"
            onClick={handleSoloDev}
          >
            {/* Glow effect on hover */}
            <div className="absolute inset-0 rounded-2xl bg-[radial-gradient(circle_at_50%_0%,rgba(199,243,107,0.06),transparent_60%)] opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            <div className="relative z-10 flex flex-col h-full">
              {/* Icon & Subtitle row */}
              <div className="flex items-start justify-between mb-5">
                <div className="p-3 rounded-xl bg-primary/10 border border-primary/20">
                  <Code2 className="w-6 h-6 text-primary" />
                </div>
                <span className="px-3 py-1 rounded-full text-[10px] font-bold font-mono tracking-wider bg-primary/10 text-primary border border-primary/20 uppercase">
                  Free forever
                </span>
              </div>

              {/* Title & Description */}
              <h3 className="font-display text-2xl font-bold text-[#f4f2e8] mb-2">
                Solo Developer
              </h3>
              <p className="text-sm text-slate-400 leading-relaxed mb-6">
                Scan your personal repositories, find vulnerabilities, and
                improve code quality. Perfect for open-source contributors and
                indie developers.
              </p>

              {/* Features */}
              <ul className="flex flex-col gap-3 mb-8 flex-1">
                <FeatureItem text="Personal repo scanning" />
                <FeatureItem text="Vulnerability detection" />
                <FeatureItem text="Dependency health" />
                <FeatureItem text="Code quality scores" />
              </ul>

              {/* CTA Button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleSoloDev();
                }}
                className="w-full py-3.5 rounded-xl bg-primary text-[#11130e] font-semibold text-sm hover:bg-primary-hover transition-all duration-200 shadow-[0_8px_32px_rgba(199,243,107,.15)] hover:shadow-[0_12px_40px_rgba(199,243,107,.25)]"
              >
                Continue as Solo Developer
              </button>
            </div>
          </motion.div>

          {/* Card 2 — Enterprise */}
          <motion.div
            variants={cardVariants}
            whileHover={{
              scale: 1.02,
              boxShadow: "0 0 48px rgba(255, 255, 255, 0.06)",
            }}
            className="group relative rounded-2xl border border-white/[0.08] bg-gradient-to-b from-[#181b14]/95 to-[#0e100c]/95 backdrop-blur-xl p-8 flex flex-col cursor-pointer transition-all duration-300 hover:border-white/20 overflow-hidden"
            onClick={handleEnterprise}
          >
            {/* Glow effect on hover */}
            <div className="absolute inset-0 rounded-2xl bg-[radial-gradient(circle_at_50%_0%,rgba(255,255,255,0.04),transparent_60%)] opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            <div className="relative z-10 flex flex-col h-full">
              {/* Icon & Subtitle row */}
              <div className="flex items-start justify-between mb-5">
                <div className="p-3 rounded-xl bg-white/[0.06] border border-white/10">
                  <Building2 className="w-6 h-6 text-slate-300" />
                </div>
                <span className="px-3 py-1 rounded-full text-[10px] font-bold font-mono tracking-wider bg-white/[0.06] text-slate-400 border border-white/10 uppercase">
                  Custom pricing
                </span>
              </div>

              {/* Title & Description */}
              <h3 className="font-display text-2xl font-bold text-[#f4f2e8] mb-2">
                Enterprise
              </h3>
              <p className="text-sm text-slate-400 leading-relaxed mb-6">
                Full compliance dashboards, team collaboration, advanced threat
                analysis, and dedicated support for your organization.
              </p>

              {/* Features */}
              <ul className="flex flex-col gap-3 mb-8 flex-1">
                <FeatureItem text="SOC2 & ISO 27001" />
                <FeatureItem text="Team RBAC" />
                <FeatureItem text="Multi-agent scanning" />
                <FeatureItem text="Priority support" />
              </ul>

              {/* CTA Button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleEnterprise();
                }}
                className="w-full py-3.5 rounded-xl bg-transparent border border-white/20 text-[#f4f2e8] font-semibold text-sm hover:bg-white/[0.06] hover:border-white/30 transition-all duration-200"
              >
                Continue as Enterprise
              </button>
            </div>
          </motion.div>
        </div>

        {/* Footer note */}
        <motion.p
          variants={itemVariants}
          className="mt-10 text-xs text-slate-600 font-mono text-center"
        >
          You can switch roles anytime from the dashboard toolbar
        </motion.p>
      </motion.div>
    </div>
  );
}
