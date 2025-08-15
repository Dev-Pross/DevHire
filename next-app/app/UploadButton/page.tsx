"use client";
import * as React from "react";
import Button from "../components/Button";
import axios from "axios";
import { supabase } from "../supabase";

// Remove S3 and next-auth imports and S3 config, as they're unused and cause errors

export default function UploadButtonPage() {
  // 3. Setup state and ref for file input and upload status
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = React.useState<string | null>(null);
  const [uploadedUrl, setUploadedUrl] = React.useState<string | null>(null);
  const [user, setUser] = React.useState<any>(null);

  React.useEffect(() => {
    supabase.auth.getUser().then((result: any) => {
      setUser(result?.data?.user ?? null);
    });
  }, []);
  // console.log("user:", user);

  // 4. Open file dialog when button is clicked
  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
  };

  // 5. Handle file selection and upload to Supabase Storage
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

      // 5b. Upload file to Supabase Storage
      const { error } = await supabase.storage
        .from("user-resume")
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

      // Optional: send the URL to your backend
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
      await axios.post("http://127.0.0.1:8000/get-jobs", {
        file_url: url,
        user_id: "tejabudumuru3@gmail.com",
        password: "S@IS@r@N3"
      });
      // console.log(res)
      // console.log("Server response:", res.data);
    } catch (err) {
      // console.error("Error sending URL to server:", err);
    }
  }

  return (
    <div>
      {/* 7. Upload button (hidden file input) */}
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
      {/* 8. Show error message if upload fails */}
      {uploadError && (
        <div className="text-red-500 mt-2">{uploadError}</div>
      )}
      {/* 9. Show success message and link if upload succeeds */}
      {uploadSuccess && (
        <div className="text-green-500 mt-2">
          {uploadSuccess}
          {/* Show link to uploaded file if available */}
          {uploadedUrl && (
            <div>
              <a
                href={uploadedUrl as string}
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
