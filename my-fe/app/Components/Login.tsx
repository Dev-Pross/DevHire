"use client";
import React, { useState } from "react";
import { supabase } from "../utiles/supabaseClient";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import Link from "next/link";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const LoginHandle = async () => {
    // console.log(`user: ${email} password: ${password}`);
    setError(null);
    try {
      if (!email || !password) {
        setError("Email and password are required");
        toast.error("Email and Password required!");
        setLoading(false);
      } else {
        setLoading(true);
        const { error: supabaseError } = await supabase.auth.signInWithPassword(
          {
            email: email,
            password: password,
          }
        );

        if (supabaseError) {
          // console.log("Supabase sign-in failed:", supabaseError.message);
          setError(supabaseError.message);
          toast.error(supabaseError.message);
          setLoading(false);
        } else {
          // console.log("Login successful");
          setTimeout(() => {
            toast.success("Login success");

            window.location.href = "/";
            // router.refresh()
            // router.push("/");

            // <Link href={"/"}> </Link>;
          }, 3000);
        }
      }
    } catch (err: any) {
      if (err && err.response && err.response.status === 401) {
        // console.log("Invalid email or password.");
        setError("Invalid email or password.");
        toast.error("Invalid email or password.");
        setLoading(false);
      } else {
        // console.log("An error occurred during signin.");
        setError("An error occurred during signin. Please try again. ");
        toast.error("An error occurred during signin. Please try again. ");
        setLoading(false);
      }
      // console.log(err);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 sm:px-6">
      <div className="w-full max-w-md">
        <div className="bg-white/5 backdrop-blur-lg p-6 sm:p-8 lg:p-10 rounded-2xl shadow-2xl border border-white/10">
          <h2 className="text-2xl sm:text-3xl font-bold text-center text-white mb-6 lg:mb-8">
            Login
          </h2>
          {error && (
            <div className="w-full text-center mb-4 p-3 bg-red-500/20 border border-red-500 rounded-lg text-red-200 text-sm">
              {error}
            </div>
          )}

          <form className="space-y-4">
            <div>
              <input
                className="shadow appearance-none border border-white/20 rounded-lg w-full bg-[#325b4b]/80 py-3 px-4 text-white leading-tight focus:outline-none focus:ring-2 focus:ring-green-500 transition-all"
                id="username"
                type="text"
                placeholder="Email"
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <input
                className="shadow appearance-none border border-white/20 rounded-lg w-full py-3 px-4 bg-[#325b4b]/80 text-white leading-tight focus:outline-none focus:ring-2 focus:ring-green-500 transition-all"
                id="password"
                type="password"
                placeholder="Password"
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div className="pt-2">
              <button
                onClick={LoginHandle}
                disabled={loading}
                className="bg-[#27db78] hover:bg-[#159950] w-full text-black font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                type="button"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg
                      className="animate-spin h-5 w-5 text-black"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="black"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                      />
                    </svg>
                    Signing in...
                  </span>
                ) : (
                  <span>Sign In</span>
                )}
              </button>
            </div>
          </form>
          <div className="w-full text-center mt-6 text-white text-sm sm:text-base">
            Don't have an account?{" "}
            <a href="/register" className="text-green-400 hover:text-green-300 font-semibold underline">
              Register
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
