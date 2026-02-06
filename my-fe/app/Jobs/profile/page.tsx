"use client";
import Image from "next/image";
import React, { useEffect, useState } from "react";
import getLoginUser from "../../utiles/getUserData";
import Navbar from "../../Components/Navbar";
import { supabase } from "../../utiles/supabaseClient";
import toast from "react-hot-toast";

const ProfilePage = () => {
  const [data, setDbData] = useState<any | null>(null);
  const [jobCount, setJobCount] = useState<string | null>(null);

  useEffect(() => {
    try {
      async function fetchData() {
        const userData = await getLoginUser();
        const id: any = userData?.data?.user;
        if (!id) return;
        const res = await fetch(`/api/User?id=${id.id}`, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        });
        const dataq = await res.json();
        setDbData(dataq.user);
      }
      fetchData();
      try {
        const jobs = sessionStorage.getItem("applied");
        if (jobs) setJobCount(jobs);
      } catch (e: any) {}
    } catch (error: any) {
      toast.error("Something went wrong, please try again later.");
    }
  }, []);

  function logoutHandler() {
    toast.error("Are you sure to logout!!");
    setTimeout(async () => {
      sessionStorage.clear();
      const { error } = await supabase.auth.signOut();
      if (error) toast.error("Error in logging out");
      window.location.href = "/";
    }, 1000);
  }

  return (
    <div className="page-section">
      <Navbar />
      <div className="min-h-screen flex flex-col lg:flex-row gap-4 md:gap-6 lg:gap-8 items-center justify-center px-4 py-8">
        {/* Profile Card */}
        <div className="surface-card p-6 md:p-8 w-full max-w-sm lg:max-w-none lg:w-auto">
          <div className="flex flex-col items-center space-y-4 md:space-y-6">
            {/* Profile Image */}
            <div className="relative group">
              <div className="absolute inset-0 bg-emerald-500/30 rounded-full blur-xl opacity-50 group-hover:opacity-75 transition duration-300" />
              <div className="relative bg-[#141414] rounded-full p-2 border-2 border-white/[0.08]">
                <div className="w-24 h-24 md:w-32 md:h-32 rounded-full overflow-hidden bg-gradient-to-br from-emerald-500/30 to-emerald-700/30 p-1">
                  <div className="w-full h-full rounded-full bg-[#141414] flex items-center justify-center">
                    <Image
                      src="/profile.svg"
                      alt="Profile"
                      width={80}
                      height={80}
                      className="rounded-full md:w-[100px] md:h-[100px]"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col gap-3 w-full">
              <button
                onClick={logoutHandler}
                className="bg-white/[0.05] hover:bg-red-500/20 border border-white/[0.08] hover:border-red-500/30 text-white font-medium py-3 px-6 rounded-xl transition-all duration-300 cursor-pointer"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="surface-card p-6 md:p-8 flex-1 max-w-3xl w-full">
          {/* Tab Header */}
          <div className="flex mb-6 md:mb-8 bg-white/[0.03] rounded-xl p-1">
            <div className="flex-1 relative">
              <button className="w-full py-2 md:py-3 px-4 md:px-6 text-black font-medium text-sm md:text-base rounded-lg bg-emerald-500 shadow-lg transition-all duration-300 cursor-default">
                Profile Info
              </button>
            </div>
          </div>

          {/* Profile Information */}
          <div className="space-y-4 md:space-y-6">
            <div className="grid gap-4 md:gap-6">
              {/* User Name */}
              <div className="group p-4 md:p-6 bg-white/[0.03] border border-white/[0.06] rounded-xl hover:bg-white/[0.05] transition-all duration-300">
                <div className="flex items-start sm:items-center justify-between gap-3">
                  <div className="flex-1">
                    <h3 className="text-xs md:text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Full Name</h3>
                    <div className="text-md w-36 md:w-100 md:text-lg lg:text-xl font-semibold text-white break-all">
                      {data?.name ? data?.name : <div className="w-32 md:w-40 h-8 md:h-10 bg-white/[0.05] rounded-lg animate-pulse" />}
                    </div>
                  </div>
                  <div className="w-10 h-10 md:w-12 md:h-12 bg-emerald-500/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg className="w-5 h-5 md:w-6 md:h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Email */}
              <div className="group p-4 md:p-6 bg-white/[0.03] border border-white/[0.06] rounded-xl hover:bg-white/[0.05] transition-all duration-300">
                <div className="flex items-start sm:items-center justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-xs md:text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Email Address</h3>
                    <div className="text-md md:text-lg lg:text-xl font-semibold text-white break-all">
                      {data?.email ? data?.email : <div className="w-36 md:w-100 h-8 md:h-10 bg-white/[0.05] rounded-lg animate-pulse" />}
                    </div>
                  </div>
                  <div className="w-10 h-10 md:w-12 md:h-12 bg-emerald-500/10 rounded-lg inline-flex items-center justify-center flex-shrink-0">
                    <svg className="w-5 h-5 md:w-6 md:h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Resume */}
              <div className="group p-4 md:p-6 bg-white/[0.03] border border-white/[0.06] rounded-xl hover:bg-white/[0.05] transition-all duration-300">
                <div className="flex items-start sm:items-center justify-between gap-3">
                  <div className="flex-1">
                    <h3 className="text-xs md:text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Resume</h3>
                    {data?.resume_url ? (
                      <div className="space-y-2">
                        <a href={data?.resume_url ? data?.resume_url : ""} target="_blank" rel="noreferrer">
                          <span className="text-white font-semibold text-sm md:text-base truncate hover:text-emerald-400 transition-colors">
                            {data?.resume_url ? "resume.pdf" : "No resume selected"}
                          </span>
                        </a>
                        <div>
                          <span className="text-emerald-300 px-2 py-1 rounded-md bg-emerald-900/40 text-xs border border-emerald-500/20">Active</span>
                        </div>
                      </div>
                    ) : (
                      <p className="w-32 md:w-40 h-8 md:h-10 bg-white/[0.05] rounded-lg animate-pulse" />
                    )}
                  </div>
                  <div className="w-10 h-10 md:w-12 md:h-12 bg-amber-500/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" className="w-5 h-5 md:w-6 md:h-6 text-amber-400">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M14 2v6h6" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Jobs Applied */}
              <div className="group p-4 md:p-6 bg-white/[0.03] border border-white/[0.06] rounded-xl hover:bg-white/[0.05] transition-all duration-300">
                <div className="flex items-start sm:items-center justify-between gap-3">
                  <div className="flex-1">
                    <h3 className="text-xs md:text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Applications Submitted</h3>
                    <div className="flex flex-wrap items-baseline gap-2">
                      <p className="text-lg md:text-xl font-bold text-white">
                        {data?.applied_jobs ? data?.applied_jobs.length : <span className="inline-block w-32 md:w-40 h-8 md:h-10 bg-white/[0.05] rounded-lg animate-pulse" />}
                      </p>
                      {data?.applied_jobs && (
                        <span className="text-emerald-900 text-xs md:text-sm font-semibold bg-emerald-400 px-2.5 py-1 rounded-full">
                          {jobCount ? `+${jobCount} now` : "0 added now"}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="w-10 h-10 md:w-12 md:h-12 bg-purple-500/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5 md:w-6 md:h-6 text-purple-400">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M20 7H4a2 2 0 00-2 2v10a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2zM16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
