import { useState, useRef } from "react";
import { supabase } from "../utiles/supabaseClient";
import toast from "react-hot-toast";

function extractFilePathFromUrl(signedUrl: string): string | null {
  try {
    // Signed URLs look like: .../storage/v1/object/sign/user-resume/filename.pdf?token=...
    const url = new URL(signedUrl);
    const pathMatch = url.pathname.match(/\/storage\/v1\/object\/sign\/user-resume\/(.+)/);
    if (pathMatch) {
      return decodeURIComponent(pathMatch[1]);
    }
    // Also handle public URLs: .../storage/v1/object/public/user-resume/filename.pdf
    const publicMatch = url.pathname.match(/\/storage\/v1\/object\/public\/user-resume\/(.+)/);
    if (publicMatch) {
      return decodeURIComponent(publicMatch[1]);
    }
    return null;
  } catch {
    return null;
  }
}

async function deleteOldResume(userId: string): Promise<void> {
  try {
    // Fetch current resume_url from user
    const res = await fetch(`/api/User?id=${userId}`, { method: "GET", credentials: "include" });
    const data = await res.json();
    const currentResumeUrl = data?.user?.resume_url;

    if (!currentResumeUrl) return;

    const filePath = extractFilePathFromUrl(currentResumeUrl);
    if (!filePath) return;

    // Delete old file from bucket
    const { error } = await supabase.storage.from("user-resume").remove([filePath]);
    if (error) {
      console.warn("Failed to delete old resume:", error.message);
      // Continue anyway - don't block upload
    }
  } catch (err) {
    console.warn("Error deleting old resume:", err);
    // Continue anyway
  }
}

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
      // Clear user_data so the backend parser knows to run Gemini for fresh details
      // on the next pipeline execution
      await fetch("/api/User?action=update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: userid,
          data: { column: "user_data", value: null },
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

    // Delete old resume before uploading new one
    if (userId) {
      await deleteOldResume(userId);
    }

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
        window.dispatchEvent(new CustomEvent("resume-uploaded"));
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
