"use client";
import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import { motion, useInView, useMotionValue, useTransform, animate } from "framer-motion";
import getLoginUser from "@/app/utiles/getUserData";

/* ── Animated Counter ── */
const AnimatedCounter = ({ target, suffix = "" }: { target: number; suffix?: string }) => {
  const count = useMotionValue(0);
  const rounded = useTransform(count, (v) => `${Math.round(v)}${suffix}`);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (isInView) {
      const controls = animate(count, target, { duration: 2, ease: "easeOut" as const });
      return controls.stop;
    }
  }, [isInView, count, target]);

  return <motion.span ref={ref}>{rounded}</motion.span>;
};

/* ── Orbiting dot ── */
const OrbitDot = ({
  radius,
  duration,
  delay,
  size,
  color,
}: {
  radius: number;
  duration: number;
  delay: number;
  size: number;
  color: string;
}) => (
  <motion.div
    className="absolute rounded-full"
    style={{
      width: size,
      height: size,
      backgroundColor: color,
      top: "50%",
      left: "50%",
    }}
    animate={{
      x: [radius, 0, -radius, 0, radius],
      y: [0, -radius, 0, radius, 0],
    }}
    transition={{ duration, repeat: Infinity, ease: "linear", delay }}
  />
);

export const HeroTalent = () => {
  const [id, setId] = useState<string | null>(null);
  const [resume, setResume] = useState<string | null>(null);

  useEffect(() => {
    async function getUser() {
      const { data, error } = await getLoginUser();
      if (data?.user) setId(data.user.id);
    }
    getUser();
  }, []);

  const checkResume = useCallback(() => {
    if (id) {
      const res = sessionStorage.getItem("resume");
      setResume(res && res !== "null" ? res : null);
    }
  }, [id]);

  useEffect(() => {
    checkResume();
  }, [checkResume]);

  useEffect(() => {
    const handleResumeUploaded = () => checkResume();
    const handleStorageChange = () => checkResume();

    window.addEventListener("resume-uploaded", handleResumeUploaded);
    window.addEventListener("storage", handleStorageChange);
    const interval = setInterval(checkResume, 2000);

    return () => {
      window.removeEventListener("resume-uploaded", handleResumeUploaded);
      window.removeEventListener("storage", handleStorageChange);
      clearInterval(interval);
    };
  }, [checkResume]);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.15, delayChildren: 0.1 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" as const } },
  };

  return (
    <section className="relative min-h-screen flex items-center overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 grid-pattern opacity-40" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[700px] bg-emerald-500/[0.06] rounded-full blur-[150px]" />
      <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-emerald-500/[0.03] rounded-full blur-[120px]" />
      <div className="absolute top-1/3 left-0 w-[300px] h-[400px] bg-emerald-600/[0.03] rounded-full blur-[100px]" />

      {/* Floating dots — animated with CSS for performance */}
      <div className="absolute top-28 right-[12%] w-2 h-2 bg-emerald-400 rounded-full animate-pulse hidden lg:block" />
      <div className="absolute top-52 right-[22%] w-1 h-1 bg-emerald-400/50 rounded-full animate-pulse hidden lg:block" style={{ animationDelay: "0.5s" }} />
      <div className="absolute top-40 left-[8%] w-1.5 h-1.5 bg-emerald-400/30 rounded-full animate-ping hidden lg:block" style={{ animationDelay: "1.5s" }} />
      <div className="absolute bottom-32 left-[15%] w-1.5 h-1.5 bg-emerald-400/40 rounded-full animate-pulse hidden lg:block" style={{ animationDelay: "2s" }} />
      <div className="absolute bottom-48 right-[8%] w-1 h-1 bg-emerald-400/60 rounded-full animate-ping hidden lg:block" style={{ animationDelay: "3s" }} />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-5 lg:px-10 py-20 lg:py-0">
        <div className="flex flex-col lg:flex-row items-center gap-12 lg:gap-16">
          {/* Left content */}
          <motion.div
            className="flex-1 max-w-2xl text-center lg:text-left"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {/* Badge */}
            <motion.div variants={itemVariants} className="mb-8">
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium backdrop-blur-sm">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
                </span>
                AI-Powered Job Automation
              </span>
            </motion.div>

            {/* Heading */}
            <motion.h1
              variants={itemVariants}
              className="text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-bold leading-[1.1] tracking-tight mb-6"
            >
              <span className="gradient-text">Find & Land Your</span>
              <br />
              <span className="gradient-text-accent">Dream Job</span>
            </motion.h1>

            {/* Subtitle */}
            <motion.p
              variants={itemVariants}
              className="text-lg lg:text-xl text-gray-400 leading-relaxed mb-10 max-w-lg mx-auto lg:mx-0"
            >
              HireHawk automates your job search — from tailoring resumes to
              applying with one click. Let AI handle the busywork.
            </motion.p>

            {/* CTA Buttons */}
            <motion.div variants={itemVariants} className="flex flex-wrap gap-4 justify-center lg:justify-start">
              {id ? (
                <>
                  <Link href="/Jobs/LinkedinUserDetails">
                    <button className="btn-primary text-base px-8 py-4">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                      </svg>
                      Upload Resume
                    </button>
                  </Link>
                  {resume && (
                    <Link href="/Jobs">
                      <button className="btn-secondary text-base px-8 py-4">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        Find Your Perfect Job
                      </button>
                    </Link>
                  )}
                </>
              ) : (
                <>
                  <Link href="/register">
                    <button className="btn-primary text-base px-8 py-4">
                      Get Started Free
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </button>
                  </Link>
                  <Link href="/login">
                    <button className="btn-secondary text-base px-8 py-4">
                      Sign In
                    </button>
                  </Link>
                </>
              )}
            </motion.div>

            {/* Animated Stats */}
            <motion.div
              variants={itemVariants}
              className="flex items-center gap-8 mt-14 justify-center lg:justify-start"
            >
              {[
                { target: 10, suffix: "K+", label: "Jobs Found" },
                { target: 95, suffix: "%", label: "Match Rate" },
                { target: 24, suffix: "/7", label: "Automation" },
              ].map((stat) => (
                <div key={stat.label} className="text-center lg:text-left group">
                  <p className="text-2xl lg:text-3xl font-bold text-white">
                    <AnimatedCounter target={stat.target} suffix={stat.suffix} />
                  </p>
                  <p className="text-sm text-gray-500">{stat.label}</p>
                </div>
              ))}
            </motion.div>
          </motion.div>

          {/* ═══════════════════════════════════════════════════════════
              Right side — Interactive Dashboard Mockup
              Animated cards with orbiting elements, progress bars, live
              status feed — feels like a real product screenshot
              ═══════════════════════════════════════════════════════════ */}
          <motion.div
            className="flex-1 relative hidden lg:flex justify-center items-center min-h-[540px]"
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.9, delay: 0.4, ease: "easeOut" as const }}
          >
            {/* Orbiting rings */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[420px] h-[420px]">
              <motion.div
                className="absolute inset-0 border border-white/[0.03] rounded-full"
                animate={{ rotate: 360 }}
                transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
              />
              <motion.div
                className="absolute inset-6 border border-emerald-500/[0.06] rounded-full"
                animate={{ rotate: -360 }}
                transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
              />
              <OrbitDot radius={200} duration={20} delay={0} size={4} color="rgba(16,185,129,0.4)" />
              <OrbitDot radius={170} duration={15} delay={3} size={3} color="rgba(16,185,129,0.25)" />
              <OrbitDot radius={130} duration={18} delay={6} size={3} color="rgba(59,130,246,0.3)" />
            </div>

            {/* ── Main Dashboard Card ── */}
            <motion.div
              className="absolute top-2 right-4 w-[290px] bg-[#111]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-2xl shadow-black/50"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.7 }}
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center">
                    <svg className="w-4 h-4 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-white text-sm font-semibold">Resume Tailored</p>
                    <p className="text-gray-500 text-[11px]">Optimized for Senior Dev</p>
                  </div>
                </div>
                <span className="text-emerald-400 text-[11px] font-bold bg-emerald-500/10 px-2 py-1 rounded-md">Live</span>
              </div>

              {/* Animated progress bar */}
              <div className="mb-4">
                <div className="flex justify-between text-[11px] mb-1.5">
                  <span className="text-gray-500">ATS Score</span>
                  <span className="text-emerald-400 font-semibold">92%</span>
                </div>
                <div className="w-full bg-white/[0.05] rounded-full h-2 overflow-hidden">
                  <motion.div
                    className="bg-gradient-to-r from-emerald-500 to-emerald-400 h-2 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: "92%" }}
                    transition={{ delay: 1.2, duration: 1.2, ease: "easeOut" as const }}
                  />
                </div>
              </div>

              {/* Skill tags */}
              <div className="flex flex-wrap gap-1.5">
                {["React", "TypeScript", "Node.js", "AWS"].map((s, i) => (
                  <motion.span
                    key={s}
                    className="px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/15 rounded-md text-[10px] text-emerald-400 font-medium"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 1.5 + i * 0.1 }}
                  >
                    {s}
                  </motion.span>
                ))}
              </div>
            </motion.div>

            {/* ── Live Activity Feed ── */}
            <motion.div
              className="absolute bottom-4 left-0 w-[265px] bg-[#111]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-4 shadow-2xl shadow-black/50"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8, duration: 0.7 }}
            >
              <p className="text-[11px] text-gray-500 font-medium uppercase tracking-wider mb-3">Live Activity</p>
              <div className="space-y-2.5">
                {[
                  { label: "Applied to Stripe", time: "Just now", color: "bg-emerald-400", icon: "✓" },
                  { label: "Match: Vercel Frontend", time: "2m ago", color: "bg-blue-400", icon: "◎" },
                  { label: "Resume updated", time: "5m ago", color: "bg-amber-400", icon: "↗" },
                ].map((item, i) => (
                  <motion.div
                    key={item.label}
                    className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/[0.02] transition-colors"
                    initial={{ opacity: 0, x: -15 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 1.0 + i * 0.15 }}
                  >
                    <div className={`w-6 h-6 rounded-lg ${item.color}/20 flex items-center justify-center shrink-0`}>
                      <span className={`text-[10px] font-bold`} style={{ color: item.color === "bg-emerald-400" ? "#34d399" : item.color === "bg-blue-400" ? "#60a5fa" : "#fbbf24" }}>{item.icon}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-white text-[11px] font-medium truncate">{item.label}</p>
                      <p className="text-gray-600 text-[9px]">{item.time}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* ── Floating Jobs Counter ── */}
            <motion.div
              className="absolute top-[45%] left-8 -translate-y-1/2 bg-[#111]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-4 shadow-2xl shadow-black/50 w-[170px]"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 1.0, duration: 0.7 }}
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 rounded-lg bg-blue-500/15 flex items-center justify-center">
                  <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M20 7H4a2 2 0 00-2 2v10a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2zM16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2" />
                  </svg>
                </div>
                <div>
                  <p className="text-white text-lg font-bold leading-none">12</p>
                  <p className="text-gray-500 text-[10px]">Applied Today</p>
                </div>
              </div>
              {/* Mini bar chart */}
              <div className="flex items-end gap-1 h-8">
                {[40, 65, 45, 80, 55, 90, 70].map((h, i) => (
                  <motion.div
                    key={i}
                    className="flex-1 bg-emerald-500/20 rounded-sm min-w-0"
                    initial={{ height: 0 }}
                    animate={{ height: `${h}%` }}
                    transition={{ delay: 1.4 + i * 0.08, duration: 0.5, ease: "easeOut" as const }}
                  />
                ))}
              </div>
              <p className="text-gray-600 text-[9px] mt-1.5">This week</p>
            </motion.div>

            {/* ── Floating notification toast ── */}
            <motion.div
              className="absolute top-0 left-1/2 -translate-x-1/2 bg-emerald-500 text-black rounded-xl px-4 py-2.5 flex items-center gap-2 shadow-lg shadow-emerald-500/30"
              initial={{ opacity: 0, y: -15, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ delay: 2.0, duration: 0.5, type: "spring", stiffness: 200 }}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-[11px] font-bold">New Match Found!</span>
            </motion.div>

            {/* ── Skills radar / match card ── */}
            <motion.div
              className="absolute bottom-2 right-8 bg-[#111]/90 backdrop-blur-xl border border-emerald-500/10 rounded-xl px-4 py-3 shadow-xl"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 1.6, duration: 0.5 }}
            >
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center text-black text-[10px] font-bold">95</div>
                <div>
                  <p className="text-white text-[11px] font-semibold">Match Score</p>
                  <p className="text-emerald-400 text-[9px]">Excellent fit</p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};
