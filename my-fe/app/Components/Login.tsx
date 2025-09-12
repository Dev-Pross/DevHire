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
    <>
      <div className="">
        <div className="p-4 showdow-sm max-w-xs mx-auto mt-10 p-10  ">
          <h2 className="text-2xl font-bold text-center text-white mb-6">
            Login
          </h2>
          {error && (
            <div className="w-full text-center mb-2 text-red-500">
              {error}!!
            </div>
          )}

          <form>
            <div className="mb-4">
              <input
                className="shadow appearance-none border rounded w-full bg-[#325b4b] py-2 px-3 text-white leading-tight border-none focus:outline-none focus:shadow-outline"
                id="username"
                type="text"
                placeholder="Email"
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="mb-6">
              <input
                className="shadow appearance-none border rounded w-full py-2 px-3 bg-[#325b4b] text-white mb-3 leading-tight border-none focus:outline-none focus:shadow-outline"
                id="password"
                type="password"
                placeholder="Password"
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div className="flex items-center justify-between px-10">
              <button
                onClick={LoginHandle}
                disabled={loading}
                className="bg-[#27db78] hover:bg-[#159950] w-full text-black font-bold py-2 px-4 rounded-4xl focus:outline-none focus:shadow-outline"
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
                  <span className="bg-black bg-clip-text text-transparent">
                    Sign In
                  </span>
                )}
              </button>
            </div>
          </form>
          <div className="w-full text-center mt-4 text-white">
            Dont have an account?{" "}
            <a href="/register" className="text-green-500">
              Register   
              
            </a>
          </div>
        </div>
      </div>
    </>
  );
};

export default Login;
