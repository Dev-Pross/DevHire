"use client";
import React, { useRef } from "react";
import { motion, useInView } from "framer-motion";

/* ═══════════════════════════════════════════════════════════
   Reference-style 2×2 Feature Cards
   Each card: illustration area (top) + title & description (bottom)
   Like the Dribbble references — clean, visual, dark theme
   ═══════════════════════════════════════════════════════════ */

/* ── Card 1: Resume Builder ── */
const ResumeVisual = () => (
  <div className="relative w-full h-full flex items-center justify-center overflow-hidden">
    {/* Multiple resume pages fanned out */}
    <motion.div
      className="absolute -rotate-6 -left-2 top-8"
      initial={{ opacity: 0, rotate: -12 }}
      whileInView={{ opacity: 0.4, rotate: -6 }}
      viewport={{ once: true }}
      transition={{ delay: 0.3 }}
    >
      <div className="w-[140px] h-[180px] bg-[#161616] border border-white/[0.05] rounded-xl p-4">
        <div className="space-y-2">
          <div className="h-2 w-16 bg-white/[0.06] rounded" />
          <div className="h-1.5 w-full bg-white/[0.04] rounded" />
          <div className="h-1.5 w-3/4 bg-white/[0.03] rounded" />
        </div>
      </div>
    </motion.div>

    {/* Main resume card */}
    <motion.div
      className="relative z-10"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: 0.15 }}
    >
      <div className="w-[170px] md:w-[190px] bg-[#161616] border border-white/[0.1] rounded-xl p-5 shadow-2xl">
        {/* Photo + Name header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center text-black text-xs font-bold">JD</div>
          <div>
            <div className="h-2.5 w-20 bg-white/25 rounded mb-1.5" />
            <div className="h-1.5 w-14 bg-white/10 rounded" />
          </div>
        </div>
        {/* Experience section */}
        <div className="mb-3">
          <div className="h-1.5 w-16 bg-emerald-500/30 rounded mb-2" />
          <div className="space-y-1.5">
            <div className="flex gap-2 items-center">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
              <div className="h-1 w-full bg-white/[0.06] rounded" />
            </div>
            <div className="flex gap-2 items-center">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400/60 shrink-0" />
              <div className="h-1 w-4/5 bg-white/[0.05] rounded" />
            </div>
            <div className="flex gap-2 items-center">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400/40 shrink-0" />
              <div className="h-1 w-full bg-white/[0.06] rounded" />
            </div>
          </div>
        </div>
        {/* Skills chips */}
        <div className="flex flex-wrap gap-1.5">
          {["React", "TS", "Node"].map((s) => (
            <span key={s} className="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 rounded text-[8px] text-emerald-400 font-medium">{s}</span>
          ))}
        </div>
      </div>

      {/* ATS Score floating badge */}
      <motion.div
        className="absolute -top-3 -right-4 bg-emerald-500 text-black text-[10px] font-bold px-3 py-1.5 rounded-lg shadow-lg shadow-emerald-500/40"
        initial={{ scale: 0 }}
        whileInView={{ scale: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.5, type: "spring", stiffness: 300 }}
      >
        ATS 92%
      </motion.div>
    </motion.div>

    {/* Third page */}
    <motion.div
      className="absolute rotate-6 -right-2 top-10"
      initial={{ opacity: 0, rotate: 12 }}
      whileInView={{ opacity: 0.3, rotate: 6 }}
      viewport={{ once: true }}
      transition={{ delay: 0.4 }}
    >
      <div className="w-[130px] h-[170px] bg-[#161616] border border-white/[0.04] rounded-xl p-4">
        <div className="space-y-2">
          <div className="h-2 w-12 bg-white/[0.05] rounded" />
          <div className="h-1.5 w-full bg-white/[0.03] rounded" />
          <div className="h-1.5 w-4/5 bg-white/[0.03] rounded" />
        </div>
      </div>
    </motion.div>

    {/* Bottom floating badge */}
    <motion.div
      className="absolute bottom-3 left-1/2 -translate-x-1/2 bg-[#1a1a1a] border border-white/[0.08] rounded-full px-4 py-1.5 flex items-center gap-2"
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: 0.6 }}
    >
      <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
      <span className="text-[10px] text-gray-400">4 templates available</span>
    </motion.div>
  </div>
);

/* ── Card 2: Skill-to-Job Matching ── */
const MatchingVisual = () => (
  <div className="relative w-full h-full flex items-center justify-center overflow-hidden px-4">
    {/* Profile card meeting job card */}
    <div className="flex items-center gap-3">
      {/* User profile mini card */}
      <motion.div
        className="w-[100px] bg-[#161616] border border-white/[0.08] rounded-xl p-3"
        initial={{ opacity: 0, x: -20 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.2 }}
      >
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600 mx-auto mb-2 flex items-center justify-center text-black text-[9px] font-bold">You</div>
        <div className="text-center space-y-1">
          <div className="h-1.5 w-12 bg-white/15 rounded mx-auto" />
          <div className="h-1 w-8 bg-white/8 rounded mx-auto" />
        </div>
        <div className="flex flex-wrap gap-1 mt-2 justify-center">
          {["JS", "TS"].map((s) => (
            <span key={s} className="px-1.5 py-0.5 bg-emerald-500/10 rounded text-[7px] text-emerald-400">{s}</span>
          ))}
        </div>
      </motion.div>

      {/* Match indicator */}
      <motion.div
        className="flex flex-col items-center gap-1"
        initial={{ opacity: 0, scale: 0.5 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.4, type: "spring" }}
      >
        <div className="w-10 h-10 rounded-full bg-emerald-500 flex items-center justify-center shadow-lg shadow-emerald-500/30">
          <svg className="w-4 h-4 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
        </div>
        <span className="text-[9px] text-emerald-400 font-semibold">Match</span>
      </motion.div>

      {/* Job card */}
      <motion.div
        className="w-[100px] bg-[#161616] border border-emerald-500/20 rounded-xl p-3 shadow-lg shadow-emerald-500/5"
        initial={{ opacity: 0, x: 20 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.2 }}
      >
        <div className="w-8 h-8 rounded-lg bg-white/[0.08] mx-auto mb-2 flex items-center justify-center">
          <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M20 7H4a2 2 0 00-2 2v10a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2zM16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2" />
          </svg>
        </div>
        <div className="text-center space-y-1">
          <div className="h-1.5 w-14 bg-white/15 rounded mx-auto" />
          <div className="h-1 w-10 bg-white/8 rounded mx-auto" />
        </div>
        <div className="flex flex-wrap gap-1 mt-2 justify-center">
          {["React", "TS"].map((s) => (
            <span key={s} className="px-1.5 py-0.5 bg-emerald-500/10 rounded text-[7px] text-emerald-400">{s}</span>
          ))}
        </div>
      </motion.div>
    </div>

    {/* Floating notifications */}
    <motion.div
      className="absolute top-4 right-4 bg-[#1a1a1a] border border-emerald-500/20 rounded-lg px-3 py-2 flex items-center gap-2"
      initial={{ opacity: 0, x: 10 }}
      whileInView={{ opacity: 0.9, x: 0 }}
      viewport={{ once: true }}
      transition={{ delay: 0.7 }}
    >
      <div className="w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center">
        <div className="w-2 h-2 rounded-full bg-emerald-400" />
      </div>
      <div>
        <p className="text-[8px] text-white font-medium">New match!</p>
        <p className="text-[7px] text-gray-500">Senior Dev at Stripe</p>
      </div>
    </motion.div>

    <motion.div
      className="absolute bottom-4 left-4 bg-[#1a1a1a] border border-white/[0.06] rounded-lg px-3 py-2 flex items-center gap-2"
      initial={{ opacity: 0, x: -10 }}
      whileInView={{ opacity: 0.7, x: 0 }}
      viewport={{ once: true }}
      transition={{ delay: 0.9 }}
    >
      <div className="w-5 h-5 rounded-full bg-blue-500/20 flex items-center justify-center">
        <div className="w-2 h-2 rounded-full bg-blue-400" />
      </div>
      <div>
        <p className="text-[8px] text-white font-medium">New match!</p>
        <p className="text-[7px] text-gray-500">Frontend at Airbnb</p>
      </div>
    </motion.div>
  </div>
);

/* ── Card 3: Tailored Applications ── */
const TailorVisual = () => (
  <div className="relative w-full h-full flex items-center justify-center overflow-hidden px-4">
    <div className="flex items-center gap-4">
      {/* Generic resume */}
      <motion.div
        className="w-[70px] bg-[#161616] border border-white/[0.06] rounded-lg p-3 opacity-60"
        initial={{ opacity: 0, x: -10 }}
        whileInView={{ opacity: 0.5, x: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.15 }}
      >
        <div className="space-y-1.5">
          <div className="h-1 w-full bg-white/[0.08] rounded" />
          <div className="h-1 w-3/4 bg-white/[0.06] rounded" />
          <div className="h-1 w-full bg-white/[0.08] rounded" />
          <div className="h-1 w-2/3 bg-white/[0.06] rounded" />
          <div className="h-1 w-full bg-white/[0.05] rounded" />
        </div>
        <p className="text-[7px] text-gray-600 mt-2 text-center">Generic</p>
      </motion.div>

      {/* AI Transform */}
      <motion.div
        className="flex flex-col items-center gap-1.5"
        initial={{ opacity: 0, scale: 0.8 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.35, type: "spring" }}
      >
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-emerald-500/20 to-emerald-500/5 border border-emerald-500/30 flex items-center justify-center">
          <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
          </svg>
        </div>
        <div className="flex gap-0.5">
          <div className="w-1 h-1 rounded-full bg-emerald-400/40 animate-pulse" />
          <div className="w-1 h-1 rounded-full bg-emerald-400/60 animate-pulse" style={{ animationDelay: "0.15s" }} />
          <div className="w-1 h-1 rounded-full bg-emerald-400/80 animate-pulse" style={{ animationDelay: "0.3s" }} />
        </div>
      </motion.div>

      {/* Tailored resume */}
      <motion.div
        className="w-[70px] bg-[#161616] border border-emerald-500/25 rounded-lg p-3 shadow-lg shadow-emerald-500/5"
        initial={{ opacity: 0, x: 10 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.15 }}
      >
        <div className="space-y-1.5">
          <div className="h-1 w-full bg-emerald-500/30 rounded" />
          <div className="h-1 w-5/6 bg-emerald-500/20 rounded" />
          <div className="h-1 w-full bg-emerald-500/30 rounded" />
          <div className="h-1 w-3/4 bg-emerald-500/20 rounded" />
          <div className="h-1 w-full bg-emerald-500/25 rounded" />
        </div>
        <p className="text-[7px] text-emerald-400 mt-2 text-center font-medium">Tailored</p>
      </motion.div>
    </div>

    {/* Keywords highlighted floating */}
    <motion.div
      className="absolute top-3 left-3 flex flex-wrap gap-1 max-w-[100px]"
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
      transition={{ delay: 0.6 }}
    >
      {["Keywords", "Matched"].map((t) => (
        <span key={t} className="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/15 rounded text-[7px] text-emerald-400/70">{t}</span>
      ))}
    </motion.div>
  </div>
);

/* ── Card 4: Smart Applier ── */
const ApplierVisual = () => (
  <div className="relative w-full h-full flex items-center justify-center overflow-hidden px-6">
    <div className="w-full max-w-[280px]">
      {/* Job listing rows being processed */}
      {[
        { company: "Stripe", role: "Sr. Frontend Dev", status: "applied", delay: 0.2 },
        { company: "Airbnb", role: "React Engineer", status: "applied", delay: 0.35 },
        { company: "Vercel", role: "Full Stack Dev", status: "applying", delay: 0.5 },
      ].map((job) => (
        <motion.div
          key={job.company}
          className="flex items-center gap-3 py-2.5 border-b border-white/[0.04] last:border-0"
          initial={{ opacity: 0, x: -10 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ delay: job.delay }}
        >
          {/* Company icon */}
          <div className="w-8 h-8 rounded-lg bg-white/[0.06] flex items-center justify-center shrink-0">
            <span className="text-[10px] font-bold text-gray-400">{job.company[0]}</span>
          </div>
          {/* Info */}
          <div className="flex-1 min-w-0">
            <p className="text-[11px] text-white font-medium truncate">{job.role}</p>
            <p className="text-[9px] text-gray-500">{job.company}</p>
          </div>
          {/* Status */}
          {job.status === "applied" ? (
            <div className="flex items-center gap-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-2.5 py-1">
              <svg className="w-2.5 h-2.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-[8px] text-emerald-400 font-medium">Applied</span>
            </div>
          ) : (
            <div className="flex items-center gap-1 bg-amber-500/10 border border-amber-500/20 rounded-full px-2.5 py-1">
              <div className="w-2 h-2 rounded-full border border-amber-400 border-t-transparent animate-spin" />
              <span className="text-[8px] text-amber-400 font-medium">Applying</span>
            </div>
          )}
        </motion.div>
      ))}

      {/* Stats footer */}
      <motion.div
        className="flex items-center justify-between mt-3 pt-3 border-t border-white/[0.06]"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.7 }}
      >
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-emerald-400" />
          <span className="text-[9px] text-gray-400"><span className="text-white font-semibold">12</span> applied today</span>
        </div>
        <span className="text-[9px] text-emerald-400 font-semibold">94% success</span>
      </motion.div>
    </div>
  </div>
);

const features = [
  {
    key: "resume",
    title: "Craft Your Perfect Resume",
    description: "Build a polished, professional resume in minutes. Our intuitive builder works for all industries — showcase your skills and stand out.",
    Visual: ResumeVisual,
    subFeatures: [
      { icon: "✦", label: "ATS-Optimized", desc: "Pass automated screening with confidence." },
      { icon: "◎", label: "Multiple Templates", desc: "Choose from professional, modern designs." },
    ],
  },
  {
    key: "matching",
    title: "AI-Powered Matching",
    description: "Our AI learns from your preferences and career path to recommend jobs that fit you best.",
    Visual: MatchingVisual,
    subFeatures: [
      { icon: "⚡", label: "Smart Analysis", desc: "Skills matched to job requirements instantly." },
      { icon: "◉", label: "Real-time Alerts", desc: "Get notified when perfect roles appear." },
    ],
  },
  {
    key: "tailor",
    title: "Tailored Applications",
    description: "HireHawk analyzes every job listing and customizes your application to highlight your most relevant strengths.",
    Visual: TailorVisual,
    subFeatures: [
      { icon: "✧", label: "Keyword Matching", desc: "Auto-highlight relevant skills & experience." },
      { icon: "↗", label: "Higher Response Rate", desc: "Tailored resumes get 3x more callbacks." },
    ],
  },
  {
    key: "applier",
    title: "The Smart Applier",
    description: "Automate applications with precision. Smart Applier fills out forms, attaches tailored docs, and tracks progress.",
    Visual: ApplierVisual,
    subFeatures: [
      { icon: "⟳", label: "Auto-Fill Forms", desc: "Intelligent field mapping across platforms." },
      { icon: "◈", label: "Track Progress", desc: "Real-time status for every application." },
    ],
  },
];

const Features = () => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section className="py-24 px-5 lg:px-10" id="features-section">
      <div className="max-w-7xl mx-auto">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium mb-6">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
            </svg>
            FEATURES
          </span>
          <h2 className="text-3xl lg:text-5xl font-bold gradient-text mb-4">
            All the Tools you need to help
          </h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Our AI job-matching bot scans thousands of listings and uses smart algorithms to find the roles that best fit your skills and preferences.
          </p>
        </motion.div>

        {/* 2×2 Feature Grid (matching reference layout) */}
        <motion.div
          ref={ref}
          className="grid grid-cols-1 md:grid-cols-2 gap-5"
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          variants={{
            hidden: { opacity: 0 },
            visible: { opacity: 1, transition: { staggerChildren: 0.12 } },
          }}
        >
          {features.map((feature) => (
            <motion.div
              key={feature.key}
              variants={{
                hidden: { opacity: 0, y: 25 },
                visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } },
              }}
              className="group relative rounded-2xl border border-white/[0.06] bg-[#111] overflow-hidden transition-all duration-500 hover:border-emerald-500/15 hover:shadow-[0_0_60px_-15px_rgba(16,185,129,0.06)]"
            >
              {/* Illustration area — top portion */}
              <div className="relative h-[220px] md:h-[260px] bg-[#0c0c0c] border-b border-white/[0.04] overflow-hidden">
                <feature.Visual />
                {/* Subtle radial glow on hover */}
                <div className="absolute inset-0 bg-radial-[at_50%_80%] from-emerald-500/[0.03] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
              </div>

              {/* Text content — bottom portion */}
              <div className="p-6 lg:p-7">
                <h3 className="text-xl font-bold text-white mb-2 group-hover:text-emerald-50 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-gray-400 text-sm leading-relaxed mb-5">
                  {feature.description}
                </p>

                {/* Sub-features row (like reference: icon + label + desc) */}
                <div className="grid grid-cols-2 gap-4">
                  {feature.subFeatures.map((sub) => (
                    <div key={sub.label} className="flex items-start gap-2.5">
                      <span className="text-emerald-400 text-sm mt-0.5 shrink-0">{sub.icon}</span>
                      <div>
                        <p className="text-white text-xs font-semibold mb-0.5">{sub.label}</p>
                        <p className="text-gray-500 text-[11px] leading-relaxed">{sub.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

export default Features;
