"use client";
import Image from "next/image";
import React, { useEffect, useRef, useState } from "react";
import getLoginUser from "../utiles/getUserData";
import Navbar from "../Components/Navbar";

const ProfilePage = () => {
  const [data, setDbData] = useState(null);
  // const id = sessionStorage.getItem("id");
  useEffect(() => {
    try {
      async function fetchData() {
        const id: any = await getLoginUser().then(
          (res) => res.data?.user.user_metadata.sub
        );
        console.log("id", id);
        if (!id) return;
        const res = await fetch(`/api/User?id=${id}`, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        });
        const dataq = await res.json();
        console.log("mydata", dataq?.user);
        setDbData(dataq);
      }
      fetchData();
    } catch (error) {
      console.error("Error fetching profile data:", error);
    }
  }, []);

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
              <button className="group relative overflow-hidden bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-medium py-3 px-6 rounded-xl transition-all duration-300 shadow-lg hover:shadow-blue-500/25 hover:-translate-y-0.5">
                <span className="relative z-10">Edit Profile</span>
              </button>
              <button className="bg-white/5 hover:bg-white/10 border border-white/20 hover:border-white/30 text-white font-medium py-3 px-6 rounded-xl transition-all duration-300 backdrop-blur-sm hover:-translate-y-0.5">
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
            <div className="flex-1">
              <button className="w-full py-3 px-6 text-white/70 font-medium rounded-lg hover:text-white hover:bg-white/5 transition-all duration-300">
                Verification
              </button>
            </div>
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
                      {data?.user?.name}
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
                      {data?.user?.email}
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
                      Phone Number
                    </h3>
                    <p className="text-xl font-semibold text-white">
                      +91 7993057519
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-gradient-to-br from-amber-500/20 to-orange-600/20 rounded-lg flex items-center justify-center">
                    <svg
                      className="w-6 h-6 text-amber-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                      />
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
                      <p className="text-3xl font-bold text-white">50</p>
                      <span className="text-green-900 text-sm font-medium bg-green-400 px-2 py-1 rounded-full">
                        +12 this month
                      </span>
                    </div>
                  </div>
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-500/20 to-pink-600/20 rounded-lg flex items-center justify-center">
                    <svg
                      className="w-6 h-6 text-purple-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 002 2h2a2 2 0 002-2V4h-2a2 2 0 00-2-2z"
                      />
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
