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
  const [renderReset, setRenderReset] = useState(false)
  const router = useRouter();
  
  const resetPassword = ()=>{
    setRenderReset(true)
  }

  useEffect(()=>{
     async function fetchUser() {
          const { data, error } = await getLoginUser();
          if (data) {
            router.push('/')
          }
        }
        fetchUser();
  })

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
        {renderReset ? (<ResetPass onBack={()=>setRenderReset(false)}/>):(
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
                <div className="relative">
                  <input
                    className="shadow appearance-none border border-white/20 rounded-lg w-full py-3 px-4 pr-12 bg-[#325b4b]/80 text-white leading-tight focus:outline-none focus:ring-2 focus:ring-green-500 transition-all"
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Password"
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors focus:outline-none"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? (
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                      </svg>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>
              <div className="w-full flex flex-row-reverse"><span onClick={resetPassword} className="px-2 text-amber-300 cursor-pointer">forgot password?</span></div>
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
        )}
      </div>
    </div>
  );
};

export default Login;
