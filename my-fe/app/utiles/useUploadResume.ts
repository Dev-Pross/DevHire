import { useState, useRef } from "react";
import { supabase } from "../utiles/supabaseClient";
import toast from "react-hot-toast";

export function useResumeUpload(userId: string | undefined) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null);

  async function resumePush(userid: string | undefined, link: string) {
    if (!userid) return;
    try {
      await fetch("/api/User?action=update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: userid,
          data: { column: "resume_url", value: link },
        }),
      });
    } catch (err) {
      toast.error("Something went wrong, please try again later")
    }
  }

  async function onUploadClick(event: React.ChangeEvent<HTMLInputElement>) {
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

      if (urlData?.signedUrl) {
        await resumePush(userId, urlData.signedUrl);
        sessionStorage.setItem("resume", urlData.signedUrl);
      }
    } catch (error: any) {
      setUploadError(`Upload failed: ${error.message || error.toString()}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return {
    fileInputRef,
    uploading,
    uploadError,
    uploadSuccess,
    uploadedUrl,
    onUploadClick,
  };
}
