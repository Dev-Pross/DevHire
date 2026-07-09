"use client";
import Image from "next/image";
import React, { useEffect, useState } from "react";
import getLoginUser from "../../utiles/getUserData";
import Navbar from "../../Components/Navbar";
import { supabase } from "../../utiles/supabaseClient";
import toast from "react-hot-toast";
import { API_URL } from "../../utiles/api";

const ProfilePage = () => {
  const [data, setDbData] = useState<any | null>(null);
  const [jobCount, setJobCount] = useState<string | null>(null);
  const [workflowHistory, setWorkflowHistory] = useState<any[]>([]);
  const [showDisconnectModal, setShowDisconnectModal] = useState<boolean>(false);

  const handleLinkedInToggle = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const isChecked = e.target.checked;
    if (isChecked) {
      if (!data?.id && !data?.email) return;
      const userIdStr = data?.id;
      const loadToast = toast.loading("Generating connection token...");
      try {
        const response = await fetch(`${API_URL}/api/linkedin/connect-token`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userIdStr })
        });
        const result = await response.json();
        if (response.ok) {
          toast.success("Token generated! Redirecting...", { id: loadToast });
          window.location.href = `/connect?token=${result.token}&stream_url=${encodeURIComponent(result.stream_server_url)}`;
        } else if (response.status === 409) {
          const remaining = result.remaining_seconds || 60;
          toast.error(`Another session is running. Wait ${remaining}s or try again later.`, { id: loadToast });
        } else {
          toast.error(result.detail || "Failed to generate token", { id: loadToast });
        }
      } catch (err: any) {
        toast.error("Failed to connect: " + err.message, { id: loadToast });
      }
    } else {
      setShowDisconnectModal(true);
    }
  };

  const confirmDisconnect = async () => {
    setShowDisconnectModal(false);
    if (!data?.id) return;
    const loadToast = toast.loading("Disconnecting LinkedIn...");
    try {
      const res = await fetch("/api/User?action=update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: data.id,
          data: { column: "linkedin_context", value: null }
        })
      });
      if (res.ok) {
        toast.success("LinkedIn disconnected successfully!", { id: loadToast });
        setDbData((prev: any) => ({ ...prev, linkedin_context: null }));
      } else {
        toast.error("Failed to disconnect", { id: loadToast });
      }
    } catch (err: any) {
      toast.error("Error: " + err.message, { id: loadToast });
    }
  };

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
                  <div className="w-full h-full rounded-full bg-[#141414] flex items-center justify-center overflow-hidden">
                    {data?.profile_image ? (
                      <img
                        src={data.profile_image}
                        alt="Profile"
                        className="w-full h-full object-cover rounded-full"
                        referrerPolicy="no-referrer"
                      />
                    ) : (
                      <Image
                        src="/profile.svg"
                        alt="Profile"
                        width={80}
                        height={80}
                        className="rounded-full md:w-[100px] md:h-[100px]"
                      />
                    )}
                  </div>
                </div>
              </div>
              
              <div className="absolute -bottom-3 z-10 flex justify-center w-full">
                {data === null ? (
                  <span className="text-[11px] font-bold px-3 py-0.5 rounded-full bg-white/[0.05] text-transparent filter blur-sm">
                    LOADING
                  </span>
                ) : (
                  <span className={`text-[11px] font-bold px-3 py-0.5 rounded-full ${data?.tier === 'PRO' ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 shadow-[0_0_12px_rgba(99,102,241,0.6)]' : 'bg-[#1A1A1A] text-gray-400 border border-white/[0.08] shadow-lg'}`}>
                    {data?.tier || 'FREE'}
                  </span>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col gap-3 w-full">
              <button
                onClick={async () => {
                  if (!data?.id && !data?.email) return;
                  const userIdStr = data?.email || data?.id;
                  const loadToast = toast.loading("Cleaning up old sessions...");
                  try {
                    const res = await fetch("/api/jobs/cleanup", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ user_id: userIdStr })
                    });
                    const result = await res.json();
                    if (res.ok) {
                      toast.success(`Cleaned up ${result.deleted_count} old sessions!`, { id: loadToast });
                    } else {
                      toast.error("Cleanup failed: " + (result.detail || "Unknown error"), { id: loadToast });
                    }
                  } catch (e: any) {
                    toast.error("Cleanup failed: " + e.message, { id: loadToast });
                  }
                }}
                className="bg-white/[0.05] hover:bg-emerald-500/20 border border-white/[0.08] hover:border-emerald-500/30 text-white font-medium py-3 px-6 rounded-xl transition-all duration-300 cursor-pointer"
              >
                Clean Old Sessions
              </button>
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

              {/* LinkedIn Connection */}
              <div className="group p-4 md:p-6 bg-white/[0.03] border border-white/[0.06] rounded-xl hover:bg-white/[0.05] transition-all duration-300">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex-1">
                    <h3 className="text-xs md:text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">LinkedIn Connection</h3>
                    <div className="flex items-center gap-3">
                      <span className={`text-xs md:text-sm font-semibold px-2.5 py-1 rounded-full ${
                        data?.linkedin_context 
                          ? "text-emerald-300 bg-emerald-950/40 border border-emerald-500/20" 
                          : "text-gray-400 bg-white/[0.03] border border-white/[0.08]"
                      }`}>
                        {data?.linkedin_context ? "Connected" : "Disconnected"}
                      </span>
                    </div>
                  </div>
                  
                  {/* Toggle Switch */}
                  <div className="flex items-center flex-shrink-0">
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={!!data?.linkedin_context} 
                        onChange={handleLinkedInToggle}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-white/[0.08] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-gray-400 peer-checked:after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Custom Disconnect Confirmation Modal */}
      {showDisconnectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="surface-card border border-white/[0.08] max-w-md w-full p-6 md:p-8 space-y-6 shadow-2xl rounded-2xl transform transition-all">
            <div className="flex items-center gap-4 text-amber-400">
              <div className="w-12 h-12 bg-amber-500/10 rounded-full flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-white">Disconnect LinkedIn?</h3>
            </div>
            
            <p className="text-gray-400 text-sm md:text-base leading-relaxed">
              Are you sure you want to disconnect your LinkedIn account? Your auto-applier bot won't be able to apply to new jobs until you reconnect.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <button
                onClick={confirmDisconnect}
                className="flex-1 bg-red-600 hover:bg-red-500 text-white font-medium py-3 px-4 rounded-xl transition-all duration-300 cursor-pointer"
              >
                Disconnect
              </button>
              <button
                onClick={() => setShowDisconnectModal(false)}
                className="flex-1 bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-white font-medium py-3 px-4 rounded-xl transition-all duration-300 cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfilePage;
