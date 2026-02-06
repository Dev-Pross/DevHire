import React, { useEffect, useState } from "react";
import { supabase } from "../utiles/supabaseClient";

interface RestProps {
  onBack: () => void;
}

const ResetPass = ({ onBack }: RestProps) => {
  const [email, setEmail] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const resendMailTime = 60000;
  const [buttonShow, setButtonShow] = useState(false);
  const [resetTimer, setResetTimer] = useState(0);

  useEffect(() => {
    if (buttonShow && resetTimer > 0) {
      const timer = setInterval(() => {
        setResetTimer((prev) => prev - 1);
      }, 1000);
      return () => clearInterval(timer);
    }
  });

  const resetPassword = async () => {
    setLoading(true);
    try {
      if (email) {
        setError("Password reset link sent to your mail");
        const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
          redirectTo: `https://dev-hire-znlr.vercel.app/reset-password`,
        });
        if (error?.message) setError(error?.message);
        setLoading(false);
      }
    } catch (e) {
      setLoading(false);
      setError(e instanceof Error ? e.message : "Unknown Error");
    }
    setButtonShow(true);
    setResetTimer(60);
    setTimeout(() => {
      setButtonShow(false);
    }, resendMailTime);
  };

  return (
    <div className="surface-card p-8 lg:p-10">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <button
          className="w-9 h-9 rounded-lg bg-white/[0.05] border border-white/[0.08] flex items-center justify-center text-gray-400 hover:text-white hover:border-white/[0.15] transition-all cursor-pointer"
          onClick={onBack}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div>
          <h2 className="text-xl font-bold text-white">Reset Password</h2>
          <p className="text-gray-500 text-sm">We&apos;ll send a reset link to your email</p>
        </div>
      </div>

      {error && (
        <div className={`mb-6 p-3 rounded-xl text-sm text-center border ${
          error.includes("sent") 
            ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
            : "bg-red-500/10 border-red-500/20 text-red-400"
        }`}>
          {error}
        </div>
      )}

      <form className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Email address</label>
          <input
            className="input-dark"
            type="email"
            placeholder="you@example.com"
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <button
          onClick={resetPassword}
          disabled={loading || buttonShow}
          className="btn-primary w-full !rounded-xl !py-3.5"
          type="button"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5 text-black" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
              Sending...
            </span>
          ) : buttonShow && resetTimer > 0 ? (
            `Resend in ${resetTimer}s`
          ) : (
            "Send Reset Link"
          )}
        </button>
      </form>
    </div>
  );
};

export default ResetPass;
