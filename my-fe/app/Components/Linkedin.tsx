"use client";
import React, { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { useResumeUpload } from "@/app/utiles/useUploadResume";

export default function LinkedinUserDetailsPage() {
  const router = useRouter();
  const [data, setData] = useState({ username: "", password: "" });
  const [ userId, setUserId]  = useState<string>("")

  async function sendCredentials(data: { username: string; password: string }) {
    try {
      const res = await fetch("/api/store", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(data),
        credentials: "include",
      });
      const json = await res.json();
      if (res.ok) {
        toast.success("Successfully submitted your data");
      } else {
        console.log("error", json.message);
        toast.error("Something went wrong, please try again later")
      }
      
    } catch (error) {
      // console.log("network error:", error);
      toast.error("Something went wrong with network, please try again later")

    }
  }

  useEffect(()=>{
    const id = sessionStorage.getItem("id")
    if(id)
      setUserId(id)
    else
      toast.error("Please login to proceed.")
  },[])


  async function handleLogin(e: React.MouseEvent<HTMLButtonElement>) {
    e.preventDefault();
    // console.log("Logging in with:", data);

    await sendCredentials(data);

    router.push("/");
  }

  // File upload handlers
  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
  };


  const {
      fileInputRef,
      uploading,
      uploadError,
      uploadSuccess,
      uploadedUrl,
      onUploadClick,
    } = useResumeUpload(userId)
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 sm:px-6">
      <div className="bg-white/5 backdrop-blur-lg p-6 sm:p-8 lg:p-10 rounded-2xl shadow-2xl border border-white/10">

      <h2 className="text-2xl sm:text-3xl font-bold text-center text-white mb-6 lg:mb-8">
            Upload your details
          </h2>

          <form className="space-y-4">
            <div>
              <label className="block mb-2 text-sm font-medium text-gray">
               Linkedin Username:
              </label>
              <input
                className="shadow appearance-none border border-white/20 rounded-lg w-full bg-[#325b4b]/80 py-3 px-4 text-white leading-tight focus:outline-none focus:ring-2 focus:ring-green-500 transition-all"
                id="username"
                type="text"
                placeholder="Enter your LinkedIn username"
                value={data.username}
                onChange={(e) => setData({ ...data, username: e.target.value })}
              />
            </div>
            <div>
              <label className="block mb-2 text-sm font-medium text-gray">
               Linkedin Password:
              </label>
              <input
                className="shadow appearance-none border border-white/20 rounded-lg w-full py-3 px-4 bg-[#325b4b]/80 text-white leading-tight focus:outline-none focus:ring-2 focus:ring-green-500 transition-all"
                id="password"
                type="password"
                placeholder="Enter your LinkedIn password"
                value={data.password}
                onChange={(e) => setData({ ...data, password: e.target.value })}
              />
            </div>

              {/* File upload section */}
              <label className="block mb-2 text-sm font-medium text-gray">
                Upload Resume (PDF):
              </label>
              <button
                type="button"
                onClick={handleFileButtonClick}
                className="w-full bg-green-500 text-white p-2 rounded hover:bg-green-600 mb-2"
                disabled={uploading}
              >
                {uploading ? "Uploading..." : "Upload Resume"}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                style={{ display: "none" }}
                onChange={onUploadClick}
              />
              {uploadError && <div className="text-red-500 mt-2">{uploadError}</div>}
              {uploadSuccess && (
                <div className="text-green-500 mt-2">
                  {uploadSuccess}
                  {uploadedUrl && (
                    <div>
                      <a
                        href={uploadedUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="underline text-blue-600 break-all"
                      >
                        View uploaded file
                      </a>
                    </div>
                  )}
                </div>
              )}

            <div className="pt-2">
              <button
                onClick={handleLogin}
                className="bg-[#27db78] hover:bg-[#159950] w-full text-black font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Submit
              </button>
            </div>
          </form>
      </div>
    </div>
  );
}
