"use client";
import React, { useRef, useState } from "react";
import Button from "../components/Button";
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";

// 1. Get S3 configuration from environment variables
const s3Endpoint = process.env.NEXT_PUBLIC_S3_ENDPOINT as string;
const s3Region = process.env.NEXT_PUBLIC_AWS_REGION as string;
const s3AccessKeyId = process.env.NEXT_PUBLIC_AWS_ACCESS_KEY_ID as string;
const s3SecretAccessKey = process.env.NEXT_PUBLIC_AWS_SECRET_ACCESS_KEY as string;
const s3Bucket = process.env.NEXT_PUBLIC_S3_BUCKET as string || "user-name";

// 2. Initialize S3 client
// to put the pdf in local storage 
const s3 = new S3Client({
  region: s3Region,
  endpoint: s3Endpoint,
  credentials: {
    accessKeyId: s3AccessKeyId,
    secretAccessKey: s3SecretAccessKey,
  },
  forcePathStyle: true,
});

export default function UploadButtonPage() {
  // 3. Setup state and ref for file input and upload status
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null);

  // 4. Open file dialog when button is clicked
  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
  };

  // 5. Handle file selection and upload to S3
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

      // 5c. Prepare upload parameters
      const uploadParams = {
        Bucket: s3Bucket,
        Key: filePath,
        Body: new Uint8Array(fileBuffer),
        ContentType: file.type,
      };

      // 5d. Upload file to S3
      await s3.send(new PutObjectCommand(uploadParams));

      // 5e. Construct public URL for uploaded file
      let fileUrl: string;
      if (s3Endpoint.endsWith("/")) {
        fileUrl = `${s3Endpoint}${s3Bucket}/${filePath}`;
      } else {
        fileUrl = `${s3Endpoint}/${s3Bucket}/${filePath}`;
      }

      setUploadSuccess(`File uploaded successfully: ${file.name}`);
      setUploadedUrl(fileUrl);
    } catch (err: any) {
      // 6. Handle upload errors
      let errorMsg = "Upload failed: ";
      if (err?.Code === "NoSuchBucket" || (err?.name === "NoSuchBucket")) {
        errorMsg += `Bucket "${s3Bucket}" not found. Please check your bucket name and that it exists.`;
      } else if (err?.message) {
        errorMsg += err.message;
      } else {
        errorMsg += JSON.stringify(err);
      }
      setUploadError(errorMsg);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

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
        accept=".pdf,.docx"
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
