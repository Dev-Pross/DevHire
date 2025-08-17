"use client";
import React, { useEffect, useRef, useState } from "react";
import Button from "../components/Button";
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import axios from "axios";
import { supabase } from "../supabase";
import { User } from "next-auth";
const s3Endpoint = process.env.NEXT_PUBLIC_S3_ENDPOINT as string;
const s3Region = process.env.NEXT_PUBLIC_AWS_REGION as string;
const s3AccessKeyId = process.env.NEXT_PUBLIC_AWS_ACCESS_KEY_ID as string;
const s3SecretAccessKey = process.env.NEXT_PUBLIC_AWS_SECRET_ACCESS_KEY as string;
const s3Bucket = process.env.NEXT_PUBLIC_S3_BUCKET as string || "user-name";

export default function UploadButtonPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  useEffect(() => {
  supabase.auth.getUser().then(({ data }) => {
    setUser(data.user);
  });
}, []);
console.log("user:", user);
  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    setUploadError(null);
    setUploadSuccess(null);
    setUploadedUrl(null);
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);

    try {
      const filePath = `${Date.now()}_${file.name}`;

      const fileBuffer = await file.arrayBuffer();

 
      const { data, error } = await supabase.storage
        .from("user-resume")            // your bucket name
        .upload(filePath, file, {
          cacheControl: "3600",
          upsert: false,
          contentType: file.type,
        });

        if (error) throw error;

      const { data: urlData, error: urlError } = await supabase.storage
        .from("user-resume")
        .createSignedUrl(filePath, 3600);

        if (urlError) throw urlError;

      setUploadSuccess(`File uploaded successfully: ${file.name}`);
      setUploadedUrl(urlData?.signedUrl || null);

      await sendUrl(urlData?.signedUrl || "");

    } catch (error: any) {
      setUploadError(`Upload failed: ${error.message || error.toString()}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  async function sendUrl(url: string) {
    if (!url) return;
    try {
      const res = await axios.post("http://127.0.0.1:8000/get-jobs", {
        file_url: url,
        user_id: "tejabudumuru3@gmail.com",
        password: "S@IS@r@N3"
      });
      console.log(res)
      console.log("Server response:", res.data);
    } catch (err) {
      console.error("Error sending URL to server:", err);
    }
  }
  
  return (
    <div>
      <Button
        disabled={uploading}
        size="lg"
        variant="primary"
        
        onClick={handleFileButtonClick}
      >
        <span>{uploading ? "Uploading..." : "Upload Resume"}</span>
      </Button>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf"
        required
        style={{ display: "none" }}
        onChange={handleFileChange}
      />
      {uploadError && (
        <div className="text-red-500 mt-2">{uploadError}</div>
      )}
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
    </div>
  );
}
