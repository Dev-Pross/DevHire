"use client";
import React, { useEffect, useState } from "react";
import { supabase } from "../utiles/supabaseClient";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import getLoginUser from "../utiles/getUserData";

const Register = () => {
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [username, setUsername] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
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

  const RegisterHandler = () => {
    setError(null);
    if (!email || !password || !confirmPassword || !username) {
      setError("All fields are required");
      toast.error("All fields are required");
      setLoading(false);
    } else if (password !== confirmPassword) {
      setError("Passwords don't match");
      toast.error("Passwords don't match");
      setLoading(false);
    } else if (!isStrongPassword(password)) {
      setError("Password should contain at least 8 characters, one uppercase, 1 lowercase, 1 digit, 1 special character");
      toast.error("Password isn't strong enough");
      setLoading(false);
    } else {
      setLoading(true);
      signUpNewUser(email, password, username);
    }
  };

  async function signUpNewUser(email: string, password: string, username: string) {
    const { data, error } = await supabase.auth.signUp({
      email: email,
      password: password,
      options: {
        data: { username: username },
        emailRedirectTo: "/login",
      },
    });
    if (error) {
      toast.error(`${error.message}, please login`);
      setLoading(false);
      setError(error.message);
    } else {
      toast.success("Registration done successfully, please login.");
      fetch("api/User?action=insert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: data.user?.user_metadata.sub,
          name: username,
          email: email,
        }),
      });
      router.push("/login");
    }
  }

  function isStrongPassword(password: string): boolean {
    return /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$/.test(password);
  }

  const EyeIcon = ({ show, toggle }: { show: boolean; toggle: () => void }) => (
    <button
      type="button"
      onClick={toggle}
      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
    >
      {show ? (
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
  );

  return (
    <div className="min-h-screen flex items-center justify-center px-4 sm:px-6 relative">
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[400px] bg-emerald-500/[0.06] rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-md relative z-10">
        <div className="surface-card p-8 lg:p-10">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-white">Create an account</h2>
            <p className="text-gray-500 text-sm mt-1">Get started with HireHawk</p>
          </div>

          {error && (
            <div className="mb-6 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center">
              {error}
            </div>
          )}

          <form className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Username</label>
              <input className="input-dark" type="text" placeholder="Enter your username" onChange={(e) => setUsername(e.target.value)} required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Email</label>
              <input className="input-dark" type="text" placeholder="you@example.com" onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Password</label>
              <div className="relative">
                <input className="input-dark !pr-12" type={showPassword ? "text" : "password"} placeholder="Create a password" onChange={(e) => setPassword(e.target.value)} required />
                <EyeIcon show={showPassword} toggle={() => setShowPassword(!showPassword)} />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Confirm Password</label>
              <div className="relative">
                <input className="input-dark !pr-12" type={showConfirmPassword ? "text" : "password"} placeholder="Confirm your password" onChange={(e) => setConfirmPassword(e.target.value)} required />
                <EyeIcon show={showConfirmPassword} toggle={() => setShowConfirmPassword(!showConfirmPassword)} />
              </div>
            </div>

            <div className="pt-1">
              <button
                onClick={RegisterHandler}
                className="btn-primary w-full !rounded-xl !py-3.5"
                type="button"
                disabled={loading}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5 text-black" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                    </svg>
                    Creating account...
                  </span>
                ) : (
                  "Create Account"
                )}
              </button>
            </div>
          </form>

          <p className="text-center mt-6 text-gray-500 text-sm">
            Already have an account?{" "}
            <a href="/login" className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors">
              Sign in
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
