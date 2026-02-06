"use client";
import React, { useEffect, useState } from "react";
import { supabase } from "../utiles/supabaseClient";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import Link from "next/link";
import ResetPass from "./ResetPass";
import getLoginUser from "../utiles/getUserData";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [renderReset, setRenderReset] = useState(false);
  const router = useRouter();

  useEffect(() => {
    async function fetchUser() {
      const { data, error } = await getLoginUser();
      if (data) {
        router.push("/");
      }
    }
    fetchUser();
  });

  const LoginHandle = async () => {
    setError(null);
    try {
      if (!email || !password) {
        setError("Email and password are required");
        toast.error("Email and Password required!");
        setLoading(false);
      } else {
        setLoading(true);
        const { error: supabaseError } = await supabase.auth.signInWithPassword({
          email: email,
          password: password,
        });

        if (supabaseError) {
          setError(supabaseError.message);
          toast.error(supabaseError.message);
          setLoading(false);
        } else {
          setTimeout(() => {
            toast.success("Login success");
            window.location.href = "/";
          }, 3000);
        }
      }
    } catch (err: any) {
      if (err && err.response && err.response.status === 401) {
        setError("Invalid email or password.");
        toast.error("Invalid email or password.");
        setLoading(false);
      } else {
        setError("An error occurred during signin. Please try again.");
        toast.error("An error occurred during signin. Please try again.");
        setLoading(false);
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 sm:px-6 relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[400px] bg-emerald-500/[0.06] rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-md relative z-10">
        {renderReset ? (
          <ResetPass onBack={() => setRenderReset(false)} />
        ) : (
          <div className="surface-card p-8 lg:p-10">
            {/* Header */}
            <div className="text-center mb-8">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-white">Welcome back</h2>
              <p className="text-gray-500 text-sm mt-1">Sign in to your account</p>
            </div>

            {error && (
              <div className="mb-6 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center">
                {error}
              </div>
            )}

            <form className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Email</label>
                <input
                  className="input-dark"
                  type="text"
                  placeholder="you@example.com"
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Password</label>
                <div className="relative">
                  <input
                    className="input-dark !pr-12"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                  >
                    {showPassword ? (
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    )}
                  </button>
                </div>
                <div className="flex justify-end mt-2">
                  <button
                    type="button"
                    onClick={() => setRenderReset(true)}
                    className="text-sm text-emerald-400 hover:text-emerald-300 transition-colors cursor-pointer"
                  >
                    Forgot password?
                  </button>
                </div>
              </div>

              <button
                onClick={LoginHandle}
                disabled={loading}
                className="btn-primary w-full !rounded-xl !py-3.5"
                type="button"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5 text-black" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                    </svg>
                    Signing in...
                  </span>
                ) : (
                  "Sign In"
                )}
              </button>
            </form>

            <p className="text-center mt-6 text-gray-500 text-sm">
              Don&apos;t have an account?{" "}
              <a href="/register" className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors">
                Sign up
              </a>
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Login;
