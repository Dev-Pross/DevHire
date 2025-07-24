"use client";
import { signIn } from "next-auth/react";
import React, { useState, useCallback } from "react";
import Link from "next/link";
import axios from "axios";
import { useRouter } from "next/navigation";
import NextAuth from "next-auth";

// SVG Eye and Eye Off Icons
const EyeIcon = ({ className = "" }) => (
  <svg
    className={className}
    width="20"
    height="20"
    viewBox="0 0 20 20"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M1 10s3.5-6 9-6 9 6 9 6-3.5 6-9 6-9-6-9-6z" />
    <circle cx="10" cy="10" r="3" />
  </svg>
);

const EyeOffIcon = ({ className = "" }) => (
  <svg
    className={className}
    width="20"
    height="20"
    viewBox="0 0 20 20"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M17.94 17.94L2.06 2.06M10 4c-5.5 0-9 6-9 6a17.6 17.6 0 0 0 3.07 3.73M6.53 6.53A3 3 0 0 0 10 13a3 3 0 0 0 2.83-2.12M14.12 14.12A8.94 8.94 0 0 1 10 16c-5.5 0-9-6-9-6a17.6 17.6 0 0 1 3.07-3.73M17.94 17.94A17.6 17.6 0 0 0 19 10s-3.5-6-9-6a8.94 8.94 0 0 0-4.12 1.12" />
  </svg>
);

// SVG Mail Icon (for email)
const MailIcon = ({ className = "" }) => (
  <svg
    className={className}
    width="22"
    height="22"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <rect x="3" y="5" width="18" height="14" rx="3" />
    <polyline points="3 7 12 13 21 7" />
  </svg>
);

// SVG Lock Icon (for password)
const LockIcon = ({ className = "" }) => (
  <svg
    className={className}
    width="22"
    height="22"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <rect x="5" y="11" width="14" height="9" rx="2" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

export default function SignIn() {
  const initialData = {
    email: "",
    password: "",
  };
  const [data, setData] = useState(initialData);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const router = useRouter();

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setData((prev) => ({
      ...prev,
      [name]: value,
    }));
  }, []);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
     const res = await  signIn( "credentials", {
        email: data.email,
        password: data.password,
        redirect: false
      });
      if(res?.ok){
        router.push("/");

      }
      else{
        setError("Invalid email or password.");

      }
    } catch (err: any) {
      if (err && err.response && err.response.status === 401) {
        setError("Invalid email or password.");
      } else {
        setError("An error occurred during signin.");
      }
      console.log(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#181c2b] via-[#101014] to-[#1a1a1a] relative overflow-hidden"
      style={{
        fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
        cursor: "default",
      }}
    >
      {/* Modern, glassy, silver-black background */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div
          className="w-full h-full"
          style={{
            background:
              "radial-gradient(ellipse 80% 60% at 50% 0%,rgba(255,255,255,0.10),rgba(0,0,0,0.7) 100%)",
            backdropFilter: "blur(18px)",
            WebkitBackdropFilter: "blur(18px)",
            transition: "background 0.3s",
          }}
        />
        {/* Silver shimmer overlay */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "linear-gradient(120deg, rgba(255,255,255,0.08) 0%, rgba(192,192,192,0.10) 40%, rgba(255,255,255,0.04) 100%)",
            mixBlendMode: "screen",
            opacity: 0.7,
          }}
        />
      </div>
      <div className="relative z-10 w-full max-w-md mx-auto flex flex-col items-center justify-center shadow-2xl rounded-3xl overflow-hidden border border-neutral-800"
        style={{
          background:
            "linear-gradient(135deg, rgba(30,32,40,0.98) 60%, rgba(24,24,28,0.98) 100%)",
          boxShadow:
            "0 8px 40px 0 rgba(0,0,0,0.45), 0 2px 8px 0 rgba(0,0,0,0.20), 0 0 0 1.5px rgba(192,192,192,0.08) inset",
          border: "1.5px solid rgba(180,180,180,0.10)",
        }}
      >
        {/* Signin Form */}
        <form
          onSubmit={handleSubmit}
          autoComplete="off"
          className="w-full px-8 py-10 flex flex-col items-center gap-6 relative z-10"
          style={{
            background:
              "linear-gradient(135deg, rgba(30,32,40,0.98) 60%, rgba(24,24,28,0.98) 100%)",
            backdropFilter: "blur(22px)",
            WebkitBackdropFilter: "blur(22px)",
          }}
        >
          <div className="w-full flex flex-col items-center mb-2">
            <div
              className="bg-gradient-to-r from-white/60 via-slate-400/40 to-white/10 rounded-full p-1.5 mb-2"
              style={{
                boxShadow: "0 2px 16px 0 rgba(255,255,255,0.10)",
                width: 56,
                height: 56,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                <circle cx="18" cy="18" r="17" stroke="url(#silver)" strokeWidth="2" fill="none"/>
                <defs>
                  <linearGradient id="silver" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#fff" />
                    <stop offset="0.5" stopColor="#bfc1c6" />
                    <stop offset="1" stopColor="#fff" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <h1
              className="text-4xl font-extrabold bg-gradient-to-r from-white via-slate-300 to-slate-400 bg-clip-text text-transparent tracking-tight select-none"
              style={{
                fontFamily: "inherit",
                letterSpacing: "-0.04em",
                textShadow: "0 2px 24px rgba(255,255,255,0.10)",
              }}
            >
              Sign In
            </h1>
            <p className="text-base font-medium text-neutral-300/90 mt-2 text-center select-none">
              Welcome back! Please sign in to your account.
            </p>
          </div>
          <div className="w-full flex flex-col gap-6">
            {/* Email */}
            <div className="relative flex items-center group">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-white transition pointer-events-none flex items-center">
                <MailIcon className="inline-block" />
              </span>
              <input
                type="email"
                name="email"
                placeholder="Enter Your Email"
                value={data.email}
                onChange={handleChange}
                required
                autoComplete="email"
                className="w-full pl-12 pr-4 py-3 rounded-xl border border-slate-700 bg-gradient-to-r from-neutral-900/80 via-neutral-800/80 to-neutral-900/80 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-200/80 focus:bg-neutral-900/90 transition-all shadow-inner font-semibold"
                spellCheck={false}
                style={{ cursor: "text", fontWeight: 500, fontSize: "1.08rem" }}
              />
            </div>
            {/* Password */}
            <div className="relative flex items-center group">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-white transition pointer-events-none flex items-center">
                <LockIcon className="inline-block" />
              </span>
              <input
                type={showPassword ? "text" : "password"}
                name="password"
                placeholder="Enter Your Password"
                value={data.password}
                onChange={handleChange}
                required
                autoComplete="current-password"
                className="w-full pl-12 pr-12 py-3 rounded-xl border border-slate-700 bg-gradient-to-r from-neutral-900/80 via-neutral-800/80 to-neutral-900/80 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-200/80 focus:bg-neutral-900/90 transition-all shadow-inner font-semibold"
                style={{ cursor: "text", fontWeight: 500, fontSize: "1.08rem" }}
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 bg-transparent border-none focus:outline-none"
                tabIndex={-1}
                aria-label={showPassword ? "Hide password" : "Show password"}
                style={{ cursor: "pointer" }}
              >
                {showPassword ? (
                  <EyeOffIcon className="text-slate-400 group-focus-within:text-white transition" />
                ) : (
                  <EyeIcon className="text-slate-400 group-focus-within:text-white transition" />
                )}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-gradient-to-r from-white/20 via-slate-400/30 to-white/10 text-white font-semibold rounded-xl shadow-lg hover:bg-white/10 hover:scale-[1.025] transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-slate-200/80 border border-slate-600/40"
            style={{
              cursor: loading ? "not-allowed" : "pointer",
              fontWeight: 600,
              fontSize: "1.13rem",
              letterSpacing: "0.01em",
              boxShadow: "0 2px 24px 0 rgba(192,192,192,0.10)",
              backgroundImage:
                "linear-gradient(90deg, rgba(255,255,255,0.13) 0%, rgba(180,180,180,0.18) 50%, rgba(255,255,255,0.08) 100%)",
            }}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
                </svg>
                Signing in...
              </span>
            ) : (
              <span className="bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                Sign In
              </span>
            )}
          </button>

          {error ? (
            <div className="w-full text-center text-red-400 bg-gradient-to-r from-red-900/40 via-red-800/30 to-red-900/40 border border-red-700/60 rounded-lg py-2 px-4 mt-2 font-semibold shadow-sm">
              {error}
            </div>
          ) : null}

          <div className="w-full flex flex-col items-center mt-4">
            <span className="text-slate-400 text-sm mb-1 select-none font-medium">Don't have an account?</span>
            <Link
              href="/signup"
              className="text-white font-semibold hover:underline hover:text-slate-200 transition"
              style={{ cursor: "pointer", fontWeight: 600 }}
            >
              Sign Up
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
