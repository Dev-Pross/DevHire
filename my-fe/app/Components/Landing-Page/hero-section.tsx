"use client";
import { useEffect } from "react";
import { supabase } from "../../utiles/supabaseClient";
import { useState } from "react";
import getLoginUser from "@/app/utiles/getUserData";
import Link from "next/link";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
export const HeroTalent = () => {
  const [id, setId] = useState<string | null>(null);
  const [resume, setResume] = useState<string | null>(null);

  useEffect(() => {
    const user = sessionStorage.getItem("id");
    if (user != "undefined") setId(user);
    else setId(null);
    const res = sessionStorage.getItem("resume");
    if (res != "undefined") setResume(res);
    else setResume(null);
  }, [id, resume]);
  return (
    <section className="min-h-screen hero w-full flex flex-col items-center justify-between px-4 sm:px-6 lg:px-12 py-12 gap-8 lg:gap-12">
      {/* Main Content Wrapper */}
      <div className="flex-1 w-full flex flex-col lg:flex-row items-center justify-center gap-8 lg:gap-16 max-w-7xl mx-auto">
        {/* Left Content */}
        <div className="flex-1 w-full lg:w-1/2 space-y-6 lg:space-y-8 text-center lg:text-left">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1
              className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-bold text-transparent leading-tight mb-4 lg:mb-6"
              style={{
                WebkitTextStroke: "2px white",
              }}
            >
              Unleash Your Potential. Land Your Job
            </h1>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-lg sm:text-xl lg:text-2xl font-extralight text-white leading-tight mb-4 lg:mb-6">
              Try Smart Applier Now
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            {id ? (
              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                <Link href={"/Jobs/LinkedinUserDetails"}>
                  <button className="w-full sm:w-auto cursor-pointer bg-gradient-to-r from-[#FFFF00] to-[#FFD700] text-black font-bold hover:from-[#FF6B35] hover:to-[#F7931E] hover:text-white transition-all duration-300 hover:scale-105 hover:shadow-2xl px-6 sm:px-8 py-3 sm:py-4 rounded-lg">
                    Upload Resume
                  </button>
                </Link>
                {resume && (
                  <Link href={"/Jobs"}>
                    <button className="w-full sm:w-auto cursor-pointer hover:bg-gray-300 text-[#1E3A8A] hover:text-[#8B5FBF] font-bold transition-all duration-300 hover:scale-105 py-3 sm:py-4 rounded-lg bg-gray-100 text-black px-6 sm:px-8">
                      Find your perfect Job
                    </button>
                  </Link>
                )}
              </div>
            ) : (
              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                <Link href="/login">
                  <button className="w-full sm:w-auto cursor-pointer bg-gradient-to-r from-[#FFFF00] to-[#FFD700] text-black font-bold hover:from-[#FF6B35] hover:to-[#F7931E] hover:text-white transition-all duration-300 hover:scale-105 hover:shadow-2xl px-6 sm:px-8 py-3 sm:py-4 rounded-lg">
                    Get Started
                  </button>
                </Link>
                <Link href="/register">
                  <button className="w-full sm:w-auto cursor-pointer hover:bg-gray-300 text-[#1E3A8A] hover:text-[#8B5FBF] font-bold transition-all duration-300 hover:scale-105 py-3 sm:py-4 rounded-lg bg-gray-100 text-black px-6 sm:px-8">
                    Upload Resume
                  </button>
                </Link>
              </div>
            )}
          </motion.div>
        </div>

        {/* Right Image */}
        <div className="w-full lg:w-2/5 flex justify-center lg:justify-end">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6 }}
            className="relative"
          >
            <img
              src="/ne.jpg"
              alt="Product showcase"
              className="w-64 h-64 sm:w-72 sm:h-72 lg:w-80 lg:h-80 xl:w-96 xl:h-96 object-cover rounded-2xl shadow-2xl"
            />
            <div className="absolute -top-4 -right-4 w-16 h-16 sm:w-20 sm:h-20 lg:w-24 lg:h-24 bg-blue-500 rounded-full opacity-20 animate-pulse"></div>
          </motion.div>
        </div>
      </div>

      {/* Bottom CTA Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.3 }}
        className="w-full pb-8 lg:pb-12 px-4 sm:px-6"
      >
        <div className="w-full text-center max-w-4xl mx-auto">
          <h2
            className="text-2xl sm:text-3xl lg:text-4xl xl:text-5xl font-thin text-transparent leading-tight mb-3 lg:mb-4"
            style={{
              WebkitTextStroke: "1px white",
            }}
          >
            Need a Perfect Resume?
          </h2>
          <p className="text-base sm:text-lg lg:text-xl font-extralight text-white leading-tight mb-4 lg:mb-6">
            Try our Resume Tailor for personalized results.
          </p>
          <Link href={"/Jobs/tailor"}>
            <button className="cursor-pointer bg-gradient-to-r from-[#10B981] to-[#059669] text-white font-bold hover:from-[#059669] hover:to-[#047857] transition-all duration-300 hover:scale-105 hover:shadow-2xl px-6 sm:px-8 py-3 sm:py-4 rounded-lg">
              Checkout our Resume Tailor
            </button>
          </Link>
        </div>
      </motion.div>
    </section>
  );
};
