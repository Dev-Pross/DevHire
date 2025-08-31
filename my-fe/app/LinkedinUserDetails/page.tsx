"use client";
import React, { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "../utiles/supabaseClient"; // adjust path as needed

export default function LinkedinUserDetailsPage() {
  const router = useRouter();
  const [data, setData] = useState({ username: "", password: "" });
  const [ userId, setUserId]  = useState<string>("")
  // File upload states
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null);

  async function sendCredentials(data: { username: string; password: string }) {
    try {
      const res = await fetch("http://localhost:3000/api/store", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(data),
        credentials: "include",
      });
      const json = await res.json();
      if (res.ok) {
        console.log("credentials stored successfully");
      } else {
        console.log("error storing credentials", json);
      }
      
    } catch (error) {
      console.log("network error:", error);
    }
  }

  useEffect(()=>{
    const id = sessionStorage.getItem("id")
    if(id)
      setUserId(id)
    else
      throw new Error("user not logged in")
  },[])

  async function resumePush(userid: any | null,link:string) {
    console.log(userid);
    
    // if(!user) return
    try{
        const res = await fetch("/api/User?action=update",
          {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({
              id: userid,
              data: {column: "resume_url", value: link}
            }),
          }
        )
      }catch(err){
        console.log(err);
        
      }
  }

  async function handleLogin(e: React.MouseEvent<HTMLButtonElement>) {
    e.preventDefault();
    console.log("Logging in with:", data);

    await sendCredentials(data);


    

    router.push("/");
  }

  // File upload handlers
  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setUploadError(null);
    setUploadSuccess(null);
    setUploadedUrl(null);
    const file = event.target.files?.[0];

    if (!file) return;

    setUploading(true);

    try {
      const filePath = `${Date.now()}_${file.name}`;

      const { data, error } = await supabase.storage
        .from("user-resume")
        .upload(filePath, file, {
          cacheControl: "3600",
          upsert: false,
          contentType: file.type,
        });

      if (error) throw error;

      const { data: urlData, error: urlError } = await supabase.storage
        .from("user-resume")
        .createSignedUrl(filePath, 8640000);

      if (urlError) throw urlError;

      setUploadSuccess(`File uploaded successfully: ${file.name}`);
      setUploadedUrl(urlData?.signedUrl || null);
      if(urlData?.signedUrl){
        await resumePush(userId,urlData?.signedUrl)
        sessionStorage.setItem("resume", urlData?.signedUrl || "");
      }
    } catch (error: any) {
      setUploadError(`Upload failed: ${error.message || error.toString()}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen ">
      <h1 className="text-3xl font-bold mb-6">LinkedIn User Details</h1>
      <p className="text-lg text-gray-700">
        This is a placeholder for LinkedIn user details.
      </p>
      <div className="mt-6 p-4 bg-white rounded shadow-md w-96">
        <label className="block mb-2 text-sm font-medium text-gray-700">
          Username:
        </label>
        <input
          type="text"
          className="w-full p-2 border border-gray-300 rounded mb-4"
          placeholder="Enter your LinkedIn username"
          value={data.username}
          onChange={(e) => setData({ ...data, username: e.target.value })}
        />
        <label className="block mb-2 text-sm font-medium text-gray-700">
          Password:
        </label>
        <input
          type="password"
          className="w-full p-2 border border-gray-300 rounded mb-4"
          placeholder="Enter your LinkedIn password"
          value={data.password}
          onChange={(e) => setData({ ...data, password: e.target.value })}
        />

        {/* File upload section */}
        <label className="block mb-2 text-sm font-medium text-gray-700">
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
          onChange={handleFileChange}
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

        <button
          onClick={handleLogin}
          className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600 mt-4"
        >
          Submit
        </button>
      </div>
    </div>
  );
}
