// "use client";
// import React, { useEffect, useRef, useState } from "react";
// // import Link from "next/link";
// import { useRouter } from "next/navigation";
// // import Button from "../components/Button";
// // import Button from "../../components/Button";
// import Button from "../Components/Button";
// import axios from "axios";
// import { supabase } from "../utiles/supabaseClient";
// // import { supabase } from "../supabase";
// // import { User } from "next-auth";
// const s3Endpoint = process.env.NEXT_PUBLIC_S3_ENDPOINT as string;
// const s3Region = process.env.NEXT_PUBLIC_AWS_REGION as string;
// const s3AccessKeyId = process.env.NEXT_PUBLIC_AWS_ACCESS_KEY_ID as string;
// const s3SecretAccessKey = process.env
//   .NEXT_PUBLIC_AWS_SECRET_ACCESS_KEY as string;
// const s3Bucket = (process.env.NEXT_PUBLIC_S3_BUCKET as string) || "user-name";

// export default function UploadButtonPage() {
// const roouter = useRouter();

//   const [url, setUrl] = useState("");
//   const fileInputRef = useRef<HTMLInputElement>(null);
//   const [uploading, setUploading] = useState(false);
//   const [uploadError, setUploadError] = useState<string | null>(null);
//   const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
//   const [uploadedUrl, setUploadedUrl] = useState<string | null>(null);
//   //   const [user, setUser] = useState<User | null>(null);
//   //   useEffect(() => {
//   //   supabase.auth.getUser().then(({ data }) => {
//   //     setUser(data.user);
//   //   });
//   // }, []);
//   // console.log("user:", user);
//   const handleFileButtonClick = () => {
//     fileInputRef.current?.click();
//   };

//   const handleFileChange = async (
//     event: React.ChangeEvent<HTMLInputElement>
//   ) => {
//     setUploadError(null);
//     setUploadSuccess(null);
//     setUploadedUrl(null);
//     const file = event.target.files?.[0];

//     if (!file) return;

//     setUploading(true);

//     try {
//       const filePath = `${Date.now()}_${file.name}`;

//       const fileBuffer = await file.arrayBuffer();

//       const { data, error } = await supabase.storage
//         .from("user-resume") // your bucket name
//         .upload(filePath, file, {
//           cacheControl: "3600",
//           upsert: false,
//           contentType: file.type,
//         });

//       if (error) throw error;

//       const { data: urlData, error: urlError } = await supabase.storage
//         .from("user-resume")
//         .createSignedUrl(filePath, 86400);

//       if (urlError) throw urlError;

//       setUploadSuccess(`File uploaded successfully: ${file.name}`);
//       setUploadedUrl(urlData?.signedUrl || null);
//       setUrl(urlData?.signedUrl || "");
//       console.log("File available at:", urlData?.signedUrl);
//       sessionStorage.setItem("resume",urlData?.signedUrl || "")
//       // await sendUrl(urlData?.signedUrl || "");

//     } catch (error: any) {
//       setUploadError(`Upload failed: ${error.message || error.toString()}`);
//     } finally {
//       setUploading(false);
//       if (fileInputRef.current) fileInputRef.current.value = "";
//     }
//   };

//   return (
//     <div className="p-40 flex justify-center">
//       <Button
//         disabled={uploading}
//         size="lg"
//         variant="primary"
//         onClick={handleFileButtonClick}
//       >
//         <span>{uploading ? "Uploading..." : "Upload Resume"}</span>
//       </Button>
//       <input
//         ref={fileInputRef}
//         type="file"
//         accept=".pdf"
//         required
//         style={{ display: "none" }}
//         onChange={handleFileChange}
//       />
//       {uploadError && <div className="text-red-500 mt-2">{uploadError}</div>}
//       {uploadSuccess && (
//         <div className="text-green-500 mt-2">
//           {uploadSuccess}
//           {uploadedUrl && (
//             <div>
//               <a
//                 href={uploadedUrl}
//                 target="_blank"
//                 rel="noopener noreferrer"
//                 className="underline text-blue-600 break-all"
//               >
//                 View uploaded file
//               </a>
//             </div>
//           )}
//         </div>
//       )}
//       <br />
//       {url && (
//         <div className="mt-4">
//           <p className="font-semibold">Uploaded File Path:</p>
//           <p className="break-all text-white">{url}</p>
//         </div>
//       )}
//       <div>
//         {/* <Link href="/joblist"> */}
//           <Button
//             disabled={uploading}
//             size="lg"
//             variant="primary"
//             onClick={() => {
//               roouter.push("/LinkedinUserDetails");
//             }}
//           >
//             {/* <span>{uploading ? "Uploading..." : "Upload Resume"}</span> */}
//             Linkdedin User Details 
//           </Button>
//         {/* </Link> */}
//       </div>
//     </div>
//   );
// }
// "use client"
import React from 'react'
import Navbar from '../Components/Navbar'
import Tailor_resume from '../Components/Tailor_resume'
// import dynamic from 'next/dynamic';

// Dynamically import Tailor_resume only on client-side
// const Tailor_resume = dynamic(() => import('../Components/Tailor_resume'), {
//   ssr: false,
// });

const page = () => {
  return (
    <div className='page-section'>
      <Navbar/>
      <Tailor_resume/>
    </div>
  )
}

export default page