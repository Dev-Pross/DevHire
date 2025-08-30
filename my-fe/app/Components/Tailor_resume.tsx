"use client"
import React, { useState } from 'react'
import Image from "next/image";

function openPDF(base64: string): void {
  const binary = atob(base64);
  const len = binary.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  const blob = new Blob([bytes], { type: 'application/pdf' });
  const url = URL.createObjectURL(blob);
  window.open(url);
}

const Tailor_resume = () => {
    const [loading, setLoading] = useState<boolean>(false)
    const tailorButton= async ()=>{
      setLoading(true)
      try{
        const response = await fetch('http://127.0.0.1:8000/tailor',{
          method:"POST",
          headers: {"Content-Type":"application/json"},
          body:JSON.stringify({
            "job_desc":"About the jobCompany DescriptionGalaxyERP Software Private Limited empowers businesses with next-generation ERP and digital solutions. We focus on redefining efficiency and innovation through seamless data integration and automation. Our state-of-the-art digital technology solutions propel businesses towards unprecedented success.Role DescriptionThis is a full-time on-site role for an ERPNext Developer located in Surat. The ERPNext Developer will be responsible for developing, customising, and optimizing GalaxyERP software solutions. Day-to-day tasks include collaborating with clients to understand their business processes, implementing ERP systems, and maintaining databases. The role also involves troubleshooting and providing technical support to ensure smooth operations.QualificationsExpertise in ERP software and Enterprise Resource Planning (ERP)Proficient in software development and customizing ERP systemsStrong understanding of business processes and optimization Experience in database management and maintenance.Excellent problem-solving skills and attention to detail.Ability to work collaboratively with a team and communicate effectively with clients.Bachelor’s degree in Computer Science, Information Technology, or related field.Experience with ERPNext is a plus",
            "resume_url":"https://uunldfxygooitgmgtcis.supabase.co/storage/v1/object/sign/user-resume/1756553349647_SRINIVAS_SAI_SARAN_TEJA_BUDUMURU.pdf?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9iZjI4OTBiZS0wYmYxLTRmNTUtOTI3Mi0xZGNiNTRmNzNhYzAiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJ1c2VyLXJlc3VtZS8xNzU2NTUzMzQ5NjQ3X1NSSU5JVkFTX1NBSV9TQVJBTl9URUpBX0JVRFVNVVJVLnBkZiIsImlhdCI6MTc1NjU1MzM1MSwiZXhwIjoxNzU2NjM5NzUxfQ.g_mMKW56Pb_ui7VabhcKYcAM5LhkENm7KCPXSJiAXOI"
          })
        });
        const data = await response.json()
        if(data.payload){
          const base64PDF = data.payload[0];

          // Decode base64 and convert to Blob
          const binary = atob(base64PDF);
          const len = binary.length;
          const bytes = new Uint8Array(len);
          for (let i = 0; i < len; i++) {
            bytes[i] = binary.charCodeAt(i);
          }

          const blob = new Blob([bytes], { type: data.media });
          const url = URL.createObjectURL(blob);
          window.open(url, "_blank");
        } else {
          console.error("Invalid response data or missing PDF");
        }
      }catch(e:any){
        console.log(e);
      }
    }
    
  

  return (
    <div className='h-screen overflow-hidden flex p-10 gap-5'>
        <div className='w-[70%] h-[80%] border border-white rounded-xl p-1'>
            <textarea name="job_description" className='bg-[#052718] text-white w-full h-full resize-none text-2xl p-4 outline-none' placeholder='enter job description'></textarea>
        </div>
        <div className='w-[30%] flex flex-col gap-10'>
        <div className='w-full h-26 border flex items-center p-2 rounded-xl border-white flex gap-2 cursor-pointer'>
            <div className='bg-red-500 h-full w-[20%] rounded-tl-xl rounded-bl-xl text-4xl p-4 content-center'>PDF</div>
            <p className='text-xl text-white'>userreumse.pdf</p>
        </div>
        <button
                onClick={tailorButton}
                className="bg-[#27db78] hover:bg-[#159950] w-[50%] h-12 text-black font-bold py-2 px-4 rounded-4xl focus:outline-none focus:shadow-outline"
                type="button"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg
                      className="animate-spin h-5 w-5 text-black"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="black"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                      />
                    </svg>
                    Tailoring...
                  </span>
                ) : (
                  <span className="bg-black bg-clip-text text-transparent ">
                      Tailor

                  </span>
                )}
        </button>

        <button
                onClick={tailorButton}
                className="bg-[#27db78] hover:bg-[#159950] w-[50%] h-12 text-black font-bold py-2 px-4 rounded-4xl focus:outline-none focus:shadow-outline"
                type="button"
              >
 
                  <span className="bg-black bg-clip-text text-transparent flex  justify-between items-center p-1">
                      Download your resume
                    <Image
                        src={"/download.svg"}
                        alt="download Icon"
                        width={30}
                        height={30}
                    >
                    </Image>
                  </span>
        </button>
        </div>
    </div>
  )
}

export default Tailor_resume