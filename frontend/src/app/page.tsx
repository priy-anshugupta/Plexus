"use client";

import React from "react";
import Link from "next/link";
import { motion, Variants } from "framer-motion";
import {
  ChevronRight,
  Menu,
  Shield,
  Network,
  ShieldCheck,
  Code,
  Check,
  Star,
} from "lucide-react";

/* ──────────────────────── Animation helpers ──────────────────────── */
const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 30 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.7, delay, ease: "easeOut" as const },
});

const stagger: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};

const staggerChild: Variants = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: "easeOut" as const } },
};

/* ──────────────────────── Data ──────────────────────── */
const NAV_LINKS = ["Features", "Pricing", "Documentation", "About"];

const FEATURES = [
  {
    Icon: Shield,
    title: "AI Security Scanning",
    desc: "Multi-agent vulnerability detection with graph-aware blast radius analysis. Find SQL injections, hardcoded secrets, and BOLA issues.",
  },
  {
    Icon: Network,
    title: "Blast Radius Mapping",
    desc: "Visualize how vulnerabilities propagate through your codebase with interactive dependency graphs and impact analysis.",
  },
  {
    Icon: ShieldCheck,
    title: "Compliance Posture",
    desc: "Real-time SOC2 and ISO 27001 compliance tracking. Automated evidence collection and audit-ready reporting.",
  },
  {
    Icon: Code,
    title: "Code Intelligence",
    desc: "Deep AST analysis, property graphs, and AI-powered code understanding. Explore your codebase like never before.",
  },
];

const TRIAGE_CATEGORIES = [
  { severity: "Critical", count: 2, color: "#ff655d", examples: "SQL Injection · Auth Bypass" },
  { severity: "High", count: 5, color: "#ffc857", examples: "Hardcoded Secrets · BOLA" },
  { severity: "Medium", count: 12, color: "#6b7280", examples: "Dependency CVEs · Misconfig" },
  { severity: "Low", count: 8, color: "#374151", examples: "Code style · Documentation" },
];

const LOGOS = ["Linear", "Vercel", "Figma", "Stripe", "Ramp", "Notion", "Loom", "Arc"];

const TESTIMONIALS = [
  {
    quote:
      "Plexus found a critical SQL injection in our auth module that three other scanners missed. The blast radius visualization alone was worth the switch.",
    name: "Sarah Chen",
    role: "VP of Engineering",
    company: "ACME CORP",
  },
  {
    quote:
      "The multi-agent scanning pipeline is unlike anything else. It understands code context, not just pattern matching.",
    name: "Marcus Rivera",
    role: "Senior Security Engineer",
    company: "NEXUS LABS",
  },
  {
    quote:
      "We went from dreading security audits to passing SOC2 in half the time. The compliance dashboard is a game-changer.",
    name: "Emily Park",
    role: "CTO",
    company: "CLOUDSHIFT",
  },
];

const PRICING_PLANS = [
  {
    tier: "Solo Developer",
    price: "Free",
    desc: "For individual developers scanning personal and open-source projects.",
    features: [
      "Up to 3 repositories",
      "Basic vulnerability scanning",
      "Dependency health checks",
      "Code quality scores",
      "Community support",
    ],
    cta: "Get Started Free",
    highlight: false,
  },
  {
    tier: "Pro",
    price: "$49/mo",
    desc: "For growing teams that need more power, integrations, and deeper insights.",
    features: [
      "Up to 20 repositories",
      "Advanced multi-agent scanning",
      "Blast radius visualization",
      "Jira & Slack integrations",
      "Standard support",
    ],
    cta: "Start Free Trial",
    highlight: true,
  },
  {
    tier: "Enterprise",
    price: "Custom",
    desc: "For teams and organizations that need compliance, collaboration, and advanced threat analysis.",
    features: [
      "Unlimited repositories",
      "SOC2 & ISO 27001 dashboards",
      "Team collaboration & RBAC",
      "Priority support & SLA",
      "Custom integrations",
    ],
    cta: "Talk to Sales",
    highlight: false,
  },
];

/* ──────────────────────── Inline SVG Logo Mark ──────────────────────── */
function PlexusLogoMark({ className = "w-8 h-8" }: { className?: string }) {
  return (
    <svg viewBox="0 0 256 256" fill="white" className={className}>
      <path d="M128 20C128 20 80 60 80 128C80 150 90 170 105 185C60 170 30 140 30 128C30 80 80 20 128 20Z" />
      <path d="M128 20C176 20 226 80 226 128C226 140 196 170 151 185C166 170 176 150 176 128C176 60 128 20 128 20Z" />
      <path d="M128 236C128 236 176 196 176 128C176 106 166 86 151 71C196 86 226 116 226 128C226 176 176 236 128 236Z" />
      <path d="M128 236C80 236 30 176 30 128C30 116 60 86 105 71C90 86 80 106 80 128C80 196 128 236 128 236Z" />
    </svg>
  );
}

/* ──────────────────────── Main Page Component ──────────────────────── */
export default function LandingPage() {
  const gradientStyle: React.CSSProperties = {
    backgroundImage:
      "linear-gradient(to right, #091020 0%, #0B2551 12.5%, #c7f36b 32.5%, #00d2ff 50%, #0B2551 67.5%, #091020 87.5%, #091020 100%)",
    backgroundSize: "200% auto",
    WebkitBackgroundClip: "text",
    backgroundClip: "text",
    color: "transparent",
    WebkitTextFillColor: "transparent",
    filter: "url(#c3-noise)",
  };

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-[#0c0c0c] text-white">
      {/* ── Background Video ── */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <video
          autoPlay
          loop
          muted
          playsInline
          className="w-full h-full object-cover pointer-events-none opacity-40"
          src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260508_064122_c4750c0e-7476-4b44-94a2-a85a65c63bf2.mp4"
        />
      </div>

      {/* ── SVG Noise Filter ── */}
      <svg className="absolute w-0 h-0">
        <filter id="c3-noise">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} stitchTiles="stitch" />
          <feColorMatrix type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.35 0" />
          <feComposite in2="SourceGraphic" operator="in" result="noise" />
          <feBlend in="SourceGraphic" in2="noise" mode="multiply" />
        </filter>
      </svg>

      {/* ── All page content sits above the video ── */}
      <div className="relative z-10">
        {/* ═══════════════════ SECTION 1 — NAVBAR ═══════════════════ */}
        <motion.nav
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" as const }}
          className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between"
        >
          {/* Left — Logo */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <PlexusLogoMark />
            <span className="text-lg font-bold tracking-tight">
              PLEXUS<span className="text-[#c7f36b]">.</span>
            </span>
          </Link>

          {/* Center — Nav Links */}
          <motion.div
            variants={stagger}
            initial="hidden"
            animate="show"
            className="hidden md:flex items-center gap-8"
          >
            {NAV_LINKS.map((link) => (
              <motion.a
                key={link}
                variants={staggerChild}
                href={`#${link.toLowerCase()}`}
                className="text-white/70 text-sm font-medium hover:text-white transition-colors"
              >
                {link}
              </motion.a>
            ))}
          </motion.div>

          {/* Right — CTA */}
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="hidden md:inline-flex items-center gap-1.5 bg-[#c7f36b] text-black text-sm font-semibold px-5 py-2 rounded-full hover:bg-[#d7ff83] transition-colors"
            >
              Get Started
              <ChevronRight className="w-4 h-4" />
            </Link>
            <button className="md:hidden p-2 text-white/70 hover:text-white">
              <Menu className="w-5 h-5" />
            </button>
          </div>
        </motion.nav>

        {/* ═══════════════════ SECTION 2 — HERO ═══════════════════ */}
        <section className="pt-16 md:pt-28 pb-20 text-center flex flex-col items-center px-6">
          <motion.h1
            {...fadeUp(0.3)}
            transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" as const }}
            className="text-4xl md:text-7xl font-semibold tracking-tight leading-[0.9]"
          >
            <span className="block">Your codebase.</span>
            <span className="block animate-shiny" style={gradientStyle}>
              Fortified.
            </span>
          </motion.h1>

          <motion.p {...fadeUp(0.5)} className="mt-8 text-white/60 max-w-md text-base leading-[1.5]">
            Plexus is the AI-native code intelligence platform. Multi-agent analysis, graph-aware
            impact mapping, and verified remediation — all in one place.
          </motion.p>

          <motion.div {...fadeUp(0.7)} className="mt-10 flex items-center gap-4 flex-wrap justify-center">
            <Link
              href="/login"
              className="inline-flex items-center gap-1.5 bg-[#c7f36b] text-black text-sm font-semibold px-7 py-3 rounded-full hover:bg-[#d7ff83] transition-colors"
            >
              Get Started
              <ChevronRight className="w-4 h-4" />
            </Link>
            <button className="inline-flex items-center gap-1.5 border border-white/20 text-white text-sm font-medium px-7 py-3 rounded-full hover:border-white/40 transition-colors">
              View Demo
            </button>
          </motion.div>

          <motion.p {...fadeUp(0.9)} className="mt-6 text-xs text-white/40">
            Free for solo developers · Enterprise plans available
          </motion.p>
        </section>

        {/* ═══════════════════ SECTION 3 — FEATURE CARDS ═══════════════════ */}
        <section id="features" className="max-w-6xl mx-auto px-6 py-20 md:py-28">
          <motion.div {...fadeUp()} className="flex items-center gap-3 mb-4">
            <span className="w-2 h-2 rounded-full bg-[#c7f36b]" />
            <span className="text-sm font-medium text-white/60">Platform</span>
            <span className="text-xs font-medium text-[#c7f36b] bg-[#c7f36b]/10 px-2.5 py-0.5 rounded-full">
              AI-native
            </span>
          </motion.div>

          <motion.h2
            {...fadeUp(0.1)}
            className="text-3xl md:text-5xl font-semibold tracking-tight mb-14"
          >
            Everything your code needs.
          </motion.h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {FEATURES.map((f, i) => (
              <motion.div
                key={f.title}
                {...fadeUp(0.1 + i * 0.1)}
                className="liquid-glass rounded-2xl p-6 group hover:bg-white/[0.03] transition-colors"
              >
                <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center mb-4 group-hover:bg-[#c7f36b]/10 transition-colors">
                  <f.Icon className="w-5 h-5 text-[#c7f36b]" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-white/50 leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ═══════════════════ SECTION 4 — TRIAGE / HOW IT WORKS ═══════════════════ */}
        <section className="max-w-6xl mx-auto px-6 py-20 md:py-28">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
            {/* Left copy */}
            <motion.div {...fadeUp()}>
              <div className="flex items-center gap-3 mb-4">
                <span className="w-2 h-2 rounded-full bg-[#c7f36b]" />
                <span className="text-sm font-medium text-white/60">Triage</span>
                <span className="text-xs font-medium text-[#c7f36b] bg-[#c7f36b]/10 px-2.5 py-0.5 rounded-full">
                  AI-native
                </span>
              </div>

              <h2 className="text-3xl md:text-5xl font-semibold tracking-tight leading-tight">
                Scan, analyze,
                <br />
                remediate.
              </h2>
              <p className="text-white/50 mt-2 text-xl font-medium">In a single pipeline.</p>
              <p className="text-white/40 mt-6 text-sm leading-relaxed max-w-md">
                Plexus orchestrates a fleet of specialized AI agents that scan your codebase in
                parallel, cross-validate findings, map blast radii across dependency graphs, and
                generate verified remediation patches — all in one automated pipeline.
              </p>

              <div className="flex flex-wrap gap-2 mt-8">
                {["Auto-categorize", "Blast radius", "AI remediation", "One-click fix"].map(
                  (chip) => (
                    <span
                      key={chip}
                      className="text-xs font-medium text-white/60 border border-white/10 px-3 py-1.5 rounded-full"
                    >
                      {chip}
                    </span>
                  )
                )}
              </div>
            </motion.div>

            {/* Right — Triage card */}
            <motion.div
              {...fadeUp(0.2)}
              className="liquid-glass rounded-2xl p-6"
            >
              <div className="flex items-center gap-2 mb-6">
                <Shield className="w-4 h-4 text-[#c7f36b]" />
                <span className="text-sm font-semibold">Vulnerability Triage</span>
                <span className="ml-auto text-xs text-white/30 font-mono">27 total</span>
              </div>

              <div className="flex flex-col gap-3">
                {TRIAGE_CATEGORIES.map((cat) => (
                  <div
                    key={cat.severity}
                    className="flex items-center gap-4 p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.05]"
                  >
                    <div
                      className="w-9 h-9 rounded-lg flex items-center justify-center text-xs font-bold shrink-0"
                      style={{ backgroundColor: `${cat.color}20`, color: cat.color }}
                    >
                      {cat.count}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium">{cat.severity}</div>
                      <div className="text-xs text-white/35 truncate">{cat.examples}</div>
                    </div>
                    <div
                      className="h-1.5 rounded-full w-20"
                      style={{ backgroundColor: `${cat.color}15` }}
                    >
                      <div
                        className="h-full rounded-full"
                        style={{
                          backgroundColor: cat.color,
                          width: `${Math.min((cat.count / 12) * 100, 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </section>

        {/* ═══════════════════ SECTION 5 — LOGO CLOUD ═══════════════════ */}
        <section className="py-20 md:py-28">
          <motion.p
            {...fadeUp()}
            className="text-xs uppercase tracking-widest text-white/40 text-center mb-12"
          >
            Built for the world&apos;s most security-conscious teams
          </motion.p>

          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="max-w-4xl mx-auto px-6 grid grid-cols-2 sm:grid-cols-4 gap-8 items-center justify-items-center"
          >
            {LOGOS.map((name) => (
              <motion.span
                key={name}
                variants={staggerChild}
                className="text-sm font-semibold tracking-tight text-white/50 hover:text-white transition-colors cursor-default select-none"
              >
                {name}
              </motion.span>
            ))}
          </motion.div>
        </section>

        {/* ═══════════════════ SECTION 6 — TESTIMONIALS ═══════════════════ */}
        <section className="max-w-6xl mx-auto px-6 py-20 md:py-28">
          <motion.div {...fadeUp()} className="flex items-center gap-3 mb-4">
            <span className="w-2 h-2 rounded-full bg-[#c7f36b]" />
            <span className="text-sm font-medium text-white/60">Testimonials</span>
          </motion.div>
          <motion.h2
            {...fadeUp(0.1)}
            className="text-3xl md:text-5xl font-semibold tracking-tight mb-14"
          >
            Loved by security teams.
          </motion.h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {TESTIMONIALS.map((t, i) => (
              <motion.div
                key={t.name}
                {...fadeUp(0.1 + i * 0.1)}
                className="liquid-glass rounded-2xl p-6 flex flex-col"
              >
                <div className="flex gap-1 mb-4">
                  {[...Array(5)].map((_, s) => (
                    <Star key={s} className="w-3.5 h-3.5 fill-[#c7f36b] text-[#c7f36b]" />
                  ))}
                </div>
                <p className="text-sm text-white/70 leading-relaxed flex-1">
                  &ldquo;{t.quote}&rdquo;
                </p>
                <div className="mt-6 pt-4 border-t border-white/[0.06]">
                  <div className="text-sm font-semibold">{t.name}</div>
                  <div className="text-xs text-white/40">
                    {t.role}, {t.company}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ═══════════════════ SECTION 7 — PRICING ═══════════════════ */}
        <section id="pricing" className="c3-pricing-section">
          {/* Watermark headline */}
          <motion.div {...fadeUp()} className="c3-watermark-container">
            <div className="c3-watermark-main">
              <span className="c3-watermark-line-1">Your codebase.</span>
              <span className="c3-watermark-line-2">Fortified.</span>
            </div>
          </motion.div>

          {/* Pricing Grid — 2 cards centered */}
          <motion.div
            {...fadeUp(0.2)}
            className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-[800px] mt-16 relative z-[3]"
          >
            {PRICING_PLANS.map((plan) => (
              <div
                key={plan.tier}
                className={`c3-card ${plan.highlight ? "c3-card-pro" : ""}`}
              >
                <span className="c3-tier-small">{plan.tier}</span>
                <div className="c3-tier-large">{plan.price}</div>
                <p className="c3-desc">{plan.desc}</p>

                <ul className="c3-list">
                  {plan.features.map((feat) => (
                    <li key={feat}>
                      <span className="c3-check">
                        <Check className="w-3.5 h-3.5 text-white" />
                      </span>
                      <span>{feat}</span>
                    </li>
                  ))}
                </ul>

                {plan.highlight ? (
                  <Link href="/login" className="c3-btn mt-auto" style={{ background: "#c7f36b", color: "#000" }}>
                    {plan.cta}
                  </Link>
                ) : (
                  <Link href="/login" className="c3-btn mt-auto">
                    {plan.cta}
                  </Link>
                )}
              </div>
            ))}
          </motion.div>
        </section>

        {/* ═══════════════════ SECTION 8 — FINAL CTA ═══════════════════ */}
        <section className="max-w-6xl mx-auto px-6 py-20 md:py-28">
          <motion.div
            {...fadeUp()}
            className="liquid-glass rounded-3xl p-10 md:p-16 text-center flex flex-col items-center relative overflow-hidden"
          >
            {/* Radial glow overlay */}
            <div
              className="absolute inset-0 pointer-events-none"
              style={{
                background:
                  "radial-gradient(ellipse at 50% 0%, rgba(199,243,107,0.08) 0%, transparent 60%)",
              }}
            />

            <h2 className="relative text-3xl md:text-5xl font-semibold tracking-tight leading-tight">
              Secure your codebase.
              <br />
              <span className="text-white/60">Ship with confidence.</span>
            </h2>
            <p className="relative mt-6 text-white/45 max-w-md text-sm leading-relaxed">
              Join thousands of developers and security teams who trust Plexus to find what others
              miss.
            </p>

            <div className="relative mt-10 flex items-center gap-4 flex-wrap justify-center">
              <Link
                href="/login"
                className="inline-flex items-center gap-1.5 bg-[#c7f36b] text-black text-sm font-semibold px-7 py-3 rounded-full hover:bg-[#d7ff83] transition-colors"
              >
                Get Started Free
                <ChevronRight className="w-4 h-4" />
              </Link>
              <button className="inline-flex items-center gap-1.5 border border-white/20 text-white text-sm font-medium px-7 py-3 rounded-full hover:border-white/40 transition-colors">
                Talk to sales
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        </section>

        {/* ═══════════════════ SECTION 9 — FOOTER ═══════════════════ */}
        <footer className="max-w-6xl mx-auto px-6 py-12 border-t border-white/[0.06]">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2.5">
              <PlexusLogoMark className="w-6 h-6" />
              <span className="text-sm font-bold tracking-tight">
                PLEXUS<span className="text-[#c7f36b]">.</span>
              </span>
            </div>

            <div className="flex items-center gap-6">
              {["Privacy", "Terms", "Security", "Status"].map((link) => (
                <a
                  key={link}
                  href="#"
                  className="text-xs text-white/40 hover:text-white/70 transition-colors"
                >
                  {link}
                </a>
              ))}
            </div>

            <p className="text-xs text-white/30">
              © {new Date().getFullYear()} Plexus. All rights reserved.
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}
