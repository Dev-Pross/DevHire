"use client"
import React, { useState } from 'react'
import Image from "next/image";

const Tailor_resume = () => {
    const resume = sessionStorage.getItem("resume")
    const [loading, setLoading] = useState<boolean>(false)
    const [ description, setDescription ] = useState<string>();
    const tailorButton= async ()=>{
      if (!resume && !description) return
      setLoading(true)
      try{
        const response = await fetch('http://127.0.0.1:8000/tailor',{
          method:"POST",
          headers: {"Content-Type":"application/json"},
          body:JSON.stringify({
            "job_desc":description,
            "resume_url": resume
          })
        });
        const data = await response.json()
        if(data.payload){
          setLoading(false)
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
            <textarea name="job_description" onChange={(e)=>{setDescription(e.target.value)}} className='bg-[#052718] text-white w-full h-full resize-none text-2xl p-4 outline-none' placeholder='enter job description'></textarea>
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