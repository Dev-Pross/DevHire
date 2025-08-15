"use client";

import { useEffect, useRef, useState } from "react";
import { supabase } from "./supabase";
import { RealNavBar } from "./components/NavBar";
import axios from "axios";
import JobsList from "./components/JobsList";

export default function Home() {
  const [user, setUser] = useState<any | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null);
  const [jobs, setJobs] = useState<any[]>([]);


  useEffect(() => {
    supabase.auth.getUser().then(({ data, error }) => {
      if (data?.user) {
        setUser(data.user.email);
      }
    });
  }, []);

  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
    console.log("button clicked")
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
      setUploadError(null);
      setUploadSuccess(null);
      setUploadedUrl(null);
      const file = event.target.files?.[0];
      if (!file) return;
  
      setUploading(true);
  
      try {
        // 5a. Generate unique file key
        const filePath = `${Date.now()}_${file.name}`;
  
        // 5b. Convert file to ArrayBuffer for upload
        const fileBuffer = await file.arrayBuffer();
  
        const { data, error } = await supabase.storage
          .from("user-resume")            // your bucket name
          .upload(filePath, file, {
            cacheControl: "3600",
            upsert: false,
            contentType: file.type,
          });
  
          if (error) throw error;
  
        // Generate signed URL valid for 1 hour (3600 seconds)
        const { data: urlData, error: urlError } = await supabase.storage
          .from("user-resume")
          .createSignedUrl(filePath, 3600);
  
          if (urlError) throw urlError;
  
        setUploadSuccess(`File uploaded successfully: ${file.name}`);
        setUploadedUrl(urlData?.signedUrl || null);
        const linkedinID: string = "tejabudumuru3@gmail.com"
        const linkedinPassword: string = ""
        // Optional: send the URL to your backend
        if( urlData?.signedUrl){
          const jobs_Data = await sendUrl(urlData?.signedUrl,linkedinID,linkedinPassword);
          setJobs(jobs_Data)
        }
  
      } catch (error: any) {
        setUploadError(`Upload failed: ${error.message || error.toString()}`);
      } finally {
        setUploading(false);
        if (fileInputRef.current) fileInputRef.current.value = "";
      }
    };

    async function sendUrl(url: string, user_id: string,password:string) {
    if (!url) return;
    try {
      const res = await axios.post("http://127.0.0.1:8000/get-jobs", {
        file_url: url,
        user_id: user_id,
        password: password
      });
      console.log(res)
      console.log("Server response:", res.data);
      if(res.status === 200) {
        return res.data.jobs || []
      }
    } catch (err) {
      console.error("Error sending URL to server:", err);
    }
  }
  return (
    <div
      className="min-h-screen w-full flex flex-col"
      style={{
        background:
          "linear-gradient(135deg, #18181b 0%, #23272f 60%, #f5f5f7 100%)",
      }}
    >
      <RealNavBar />
      { jobs.length > 0 ? (
        <JobsList jobs={jobs} />):
        (
            <main className="flex flex-1 flex-col items-center justify-center px-4 py-12">
              <div className="bg-white/10 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 max-w-2xl w-full p-10 flex flex-col items-center">
                <h1 className="w-full flex flex-col items-center text-5xl font-extrabold mb-4 tracking-tight drop-shadow-lg">
                  <span
                    className="text-center bg-gradient-to-r from-[#C0C0C0] via-[#e5e5e5] to-[#f5f5f7] bg-clip-text text-transparent"
                    style={{
                      WebkitBackgroundClip: "text",
                      WebkitTextFillColor: "transparent",
                      backgroundClip: "text",
                    }}
                  >
                    Welcome to Automate Job
                  </span>
                </h1>

                <p className="text-lg text-gray-200 mb-8 text-center max-w-xl">
                  Experience a premium, modern, and minimal interface. Enjoy seamless
                  navigation and a luxurious black & white theme with subtle gradients
                  and glassy effects.
                </p>

                {!user ? (
                  <a
                    href="/api/auth/signin"
                    className="px-8 py-3 rounded-full bg-white/90 text-black font-semibold shadow-lg hover:bg-white transition-all duration-200"
                  >
                    Get Started
                  </a>
                ) : (
                  <div className="flex flex-col items-center">
                    <span className="text-white text-xl mb-2">
                      Hello, <span className="font-bold">{user}</span>
                    </span>
                    <button
                      // href="UploadButton"
                      disabled={uploading}
                      onClick={()=>handleFileButtonClick()}
                      className="px-8 py-3 rounded-full bg-black/80 text-white font-semibold shadow-lg hover:bg-black transition-all duration-200 border border-white/10"
                    >
                      <span>{uploading ? "Uploading..." : "Upload Resume"}</span>
                    </button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf"
                      required
                      style={{ display: "none" }}
                      onChange={handleFileChange}
                    />
                  </div>
                )}
              </div>

              

              <footer className="mt-16 text-gray-400 text-sm">
                &copy; {new Date().getFullYear()} Premium Next App. All rights reserved.
              </footer>
            </main>
        )

        }
      
    </div>
  );
}
