"use client";
import React, { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { useResumeUpload } from "@/app/utiles/useUploadResume";

export default function LinkedinUserDetailsPage() {
  const router = useRouter();
  const [data, setData] = useState({ username: "", password: "" });
  const [userId, setUserId] = useState<string>("");
  const [showPassword, setShowPassword] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(false);

  async function sendCredentials(data: { username: string; password: string }) {
    try {
      const res = await fetch("/api/store", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(data),
        credentials: "include",
      });
      const json = await res.json();
      if (res.ok || uploadStatus) {
        toast.success("Successfully submitted your data");
      } else {
        console.log("error", json.message);
        toast.error("Something went wrong, please try again later");
      }
    } catch (error) {
      toast.error("Something went wrong with network, please try again later");
    }
  }

  useEffect(() => {
    const id = sessionStorage.getItem("id");
    if (id) setUserId(id);
    else toast.error("Please login to proceed.");
  }, []);

  async function handleLogin(e: React.MouseEvent<HTMLButtonElement>) {
    e.preventDefault();
    const res = await fetch(`/api/User?id=${userId}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    });
    const DBdata = await res.json();
    if (DBdata.user.linkedin_context) {
      console.log("login context available");
    } else {
      console.log("sending to store data");
      await sendCredentials(data);
    }
    router.push("/");
  }

  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
    setUploadStatus(true);
  };

  const { fileInputRef, uploading, uploadError, uploadSuccess, uploadedUrl, onUploadClick } = useResumeUpload(userId);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 sm:px-6">
      <div className="surface-card p-6 sm:p-8 lg:p-10 w-full max-w-md">
        <h2 className="text-2xl sm:text-3xl font-bold text-center text-white mb-6 lg:mb-8">
          Upload your details
        </h2>

        <form className="space-y-4">
          <div>
            <label className="block mb-2 text-sm font-medium text-gray-400">
              LinkedIn Username:
            </label>
            <input
              className="input-dark"
              id="username"
              type="text"
              placeholder="Enter your LinkedIn username"
              value={data.username}
              onChange={(e) => setData({ ...data, username: e.target.value })}
            />
          </div>
          <div>
            <label className="block mb-2 text-sm font-medium text-gray-400">
              LinkedIn Password:
            </label>
            <div className="relative">
              <input
                className="input-dark pr-12"
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your LinkedIn password"
                value={data.password}
                onChange={(e) => setData({ ...data, password: e.target.value })}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors focus:outline-none cursor-pointer"
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

          {/* File upload section */}
          <div>
            <label className="block mb-2 text-sm font-medium text-gray-400">
              Upload Resume (PDF):
            </label>
            <button
              type="button"
              onClick={handleFileButtonClick}
              className="w-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 font-medium p-3 rounded-xl hover:bg-emerald-500/30 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={uploading}
            >
              {uploading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                  </svg>
                  Uploading...
                </span>
              ) : (
                "Upload Resume"
              )}
            </button>
            <input ref={fileInputRef} type="file" accept=".pdf" style={{ display: "none" }} onChange={onUploadClick} />
            {uploadError && <div className="text-red-400 mt-2 text-sm">{uploadError}</div>}
            {uploadSuccess && (
              <div className="text-emerald-400 mt-2 text-sm">
                {uploadSuccess}
                {uploadedUrl && (
                  <div className="mt-1">
                    <a href={uploadedUrl} target="_blank" rel="noopener noreferrer" className="underline text-emerald-300 hover:text-emerald-200 break-all text-xs">
                      View uploaded file
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="pt-2">
            <button
              onClick={handleLogin}
              className="btn-primary w-full !py-3"
            >
              Submit
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
