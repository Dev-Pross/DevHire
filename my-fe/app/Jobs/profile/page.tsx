"use client";
import Image from "next/image";
import React, { useEffect, useRef, useState } from "react";
import getLoginUser from "../../utiles/getUserData";
import Navbar from "../../Components/Navbar";
import { error } from "console";
import { supabase } from "../../utiles/supabaseClient";

const ProfilePage = () => {
  const [data, setDbData] = useState< any | null>(null);
  const [resume, setPhone] = useState<string | null>(null)
  const [jobCount, setJobCount] = useState<string | null>(null)
  // const id = sessionStorage.getItem("id");
  useEffect(() => {
    try {
      async function fetchData() {
        const userData = await getLoginUser();
        const id: any = userData?.data?.user     
        console.log("id", id);
        if (!id) return;

      
        const res = await fetch(`/api/User?id=${id.id}`, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        });
        const dataq = await res.json();
        console.log("mydata", dataq?.user);
        setDbData(dataq.user);
      }
      fetchData();
      try{
        const jobs = sessionStorage.getItem("applied")
        if(jobs) setJobCount(jobs)
      }
      catch(e: any){
        console.error("fetcing from sessionStorage failed: ",e);
        
      }
    } catch (error) {
      console.error("Error fetching profile data:", error);
    }
  }, []);

  function logoutHandler() {
      console.log("Are you sure to logout!!");
      setTimeout(async()=>{
        sessionStorage.clear()
        const {error} = await supabase.auth.signOut()
        if(error) console.log("error in loggin out: ",error);
        window.location.href = "/"
      },1000)
    }

  return (
    <div className="page-section">
      <Navbar />
      <div className="min-h-screen flex gap-8 items-center justify-center px-4 py-8">
        {/* Profile Card */}
        <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl">
          <div className="flex flex-col items-center space-y-6">
            {/* Profile Image */}
            <div className="relative group">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full blur opacity-75 group-hover:opacity-100 transition duration-300"></div>
              <div className="relative bg-slate-800 rounded-full p-2 border-2 border-white/20">
                <div className="w-32 h-32 rounded-full overflow-hidden bg-gradient-to-br from-blue-500 to-purple-600 p-1">
                  <div className="w-full h-full rounded-full bg-slate-800 flex items-center justify-center">
                    <Image
                      src="/profile.svg"
                      alt="Profile"
                      width={100}
                      height={100}
                      className="rounded-full"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col gap-3 w-full">
              {/* <button className="group relative overflow-hidden bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-medium py-3 px-6 rounded-xl transition-all duration-300 shadow-lg hover:shadow-blue-500/25 hover:-translate-y-0.5">
                <span className="relative z-10">Edit Profile</span>
              </button> */}
              <button onClick={logoutHandler} className="bg-white/5 hover:bg-red border border-white/20 hover:border-white/30 text-white font-medium py-3 px-6 rounded-xl transition-all duration-300 backdrop-blur-sm hover:-translate-y-0.5">
                Sign Out
              </button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl flex-1 max-w-3xl">
          {/* Tab Header */}
          <div className="flex mb-8 bg-white/5 rounded-xl p-1">
            <div className="flex-1 relative">
              <button className="w-full py-3 px-6 text-white font-medium rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 shadow-lg transition-all duration-300">
                Profile Info
              </button>
            </div>
            {/* <div className="flex-1">
              <button className="w-full py-3 px-6 text-white/70 font-medium rounded-lg hover:text-white hover:bg-white/5 transition-all duration-300">
                Verification
              </button>
            </div>*/}
          </div> 

          {/* Profile Information */}
          <div className="space-y-6">
            <div className="grid gap-6">
              {/* User Name */}
              <div className="group p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:bg-white/10 transition-all duration-300">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-white/60 uppercase tracking-wider mb-2">
                      Full Name
                    </h3>
                    <p className="text-xl font-semibold text-white">
                      {data?.name ? (data?.name) : (<p className="w-40 h-10 bg-white/5 rounded-lg animate-pulse"></p>)}
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500/20 to-purple-600/20 rounded-lg flex items-center justify-center">
                    <svg
                      className="w-6 h-6 text-blue-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                      />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Email */}
              <div className="group p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:bg-white/10 transition-all duration-300">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-white/60 uppercase tracking-wider mb-2">
                      Email Address
                    </h3>
                    <p className="text-xl font-semibold text-white">
                      {data?.email ? (data?.email) : (<p className="w-100 h-10 bg-white/5 rounded-lg animate-pulse"></p>)}
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-gradient-to-br from-green-500/20 to-emerald-600/20 rounded-lg flex items-center justify-center">
                    <svg
                      className="w-6 h-6 text-green-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                      />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Phone */}
              <div className="group p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:bg-white/10 transition-all duration-300">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-white/60 uppercase tracking-wider mb-2">
                    Resume
                    </h3>
                    {data?.resume_url ? (
                      <>
                        <a href={data?.resume_url? data?.resume_url : ""} target='_blank'>
                        <span className="text-white font-semibold text-base truncate">
                          {data?.resume_url ? "resume.pdf" : 'No resume selected'}
                        </span>
                        </a>
                        
                        <div>
                          <span className="ml-auto text-green-300 px-2 py-1 rounded bg-green-900/60 text-xs">
                            Current Resume
                          </span>
                        </div>
                      </>
                      ) : (<p className="w-40 h-10 bg-white/5 rounded-lg animate-pulse"></p>)}
                  </div>
                  <div className="w-12 h-12 bg-gradient-to-br from-amber-500/20 to-orange-600/20 rounded-lg flex items-center justify-center">

                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" className="w-6 h-6 text-amber-400">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M14 2v6h6" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Jobs Applied */}
              <div className="group p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:bg-white/10 transition-all duration-300">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-white/60 uppercase tracking-wider mb-2">
                      Applications Submitted
                    </h3>
                    <div className="flex items-baseline gap-2">
                      <p className="text-3xl font-bold text-white">{data?.applied_jobs ? (data?.applied_jobs.length) : (<p className="w-40 h-10 bg-white/5 rounded-lg animate-pulse"></p>)}</p>
                      {data?.applied_jobs && (<span className="text-green-900 text-sm font-medium bg-green-400 px-2 py-1 rounded-full">
                        {jobCount ?  (`+${jobCount} now`) :("0 added now")}
                      </span>)}
                    </div>
                  </div>
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-500/20 to-pink-600/20 rounded-lg flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" stroke="currentColor" id="Briefcase-Light--Streamline-Phosphor"  className="w-6 h-6 text-purple-400">
                      <desc>
                        Briefcase Light Streamline Icon: https://streamlinehq.com
                      </desc>
                      <path d="M6.30901875 7.3851c0 -0.25469375 0.2064875 -0.46116875 0.461175 -0.46118125h2.4596125c0.3550125 0 0.57689375 0.38431875 0.3993875 0.69176875 -0.08238125 0.1426875 -0.234625 0.2305875 -0.3993875 0.2305875h-2.4596125c-0.25470625 0.0000125 -0.461175 -0.20646875 -0.461175 -0.461175ZM15.84 4.3105875v9.83843125c0 0.5943 -0.481775 1.07608125 -1.076075 1.07608125H1.23608125c-0.59430625 0 -1.07608125 -0.48178125 -1.07608125 -1.07608125V4.3105875c0 -0.59431875 0.48175625 -1.07610625 1.07608125 -1.076075H4.4643125V2.46588125c0 -0.9339 0.75708125 -1.69098125 1.69098125 -1.69098125h3.6894125c0.9339 0 1.69098125 0.75708125 1.69098125 1.69098125v0.76863125h3.22823125c0.5942875 0.000025 1.07608125 0.48179375 1.07608125 1.076075ZM5.38666875 3.2345125h5.2266625V2.46588125c0 -0.4245 -0.344125 -0.768625 -0.768625 -0.768625H6.15529375c-0.4245 0 -0.768625 0.344125 -0.768625 0.768625ZM1.08235 4.3105875v3.28895625C3.200125 8.77004375 5.58028125 9.38386875 8 9.38353125c2.41981875 0.0004 4.8000625 -0.61370625 6.91764375 -1.78475625v-3.2881875c0 -0.0849 -0.068825 -0.15371875 -0.153725 -0.153725H1.23608125c-0.08490625 -0.00000625 -0.15373125 0.068825 -0.15373125 0.153725Zm13.8353 9.83843125v-5.505675C12.77543125 9.7359375 10.40475625 10.30566875 8 10.30588125c-2.40479375 0.0002625 -4.77536875 -0.5692125 -6.91765 -1.66176875v5.50490625c0 0.08490625 0.068825 0.15373125 0.15373125 0.153725h13.5278375c0.0849 0 0.15373125 -0.068825 0.15373125 -0.153725Z" stroke-width="0.0625"></path>
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
