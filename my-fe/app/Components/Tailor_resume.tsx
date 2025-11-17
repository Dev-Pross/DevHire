"use client"
import React, { useEffect, useRef, useState } from 'react'
import { useResumeUpload } from '../utiles/useUploadResume';
import toast from 'react-hot-toast';
import { API_URL } from '../utiles/api';

const Tailor_resume = () => {
    const resume = sessionStorage.getItem("resume")
    const [loading, setLoading] = useState<boolean>(false)
    const [ description, setDescription ] = useState<string>();
    const [selectedTemplate, setSelectedTemplate] = useState<number>(0);
    const [tailoredUrl, setTailoredUrl] = useState<string | null>(null)
    const [ userId, setUserId]  = useState<string>("")
    
    
    // Your resume templates data
    const resumeTemplates = [
        {
            id: 0,
            name: "Template 0",
            preview: "/templete-0.png", // Replace with your actual image paths
            description: "Professional Modern Template"
        },
        {
            id: 1,
            name: "Template 1",
            preview: "/templete-1.png", // Replace with your actual image paths
            description: "Professional Modern Template"
        },
        {
            id: 2,
            name: "Template 2", 
            preview: "/templete-2.png", // Replace with your actual image paths
            description: "Creative Design Template"
        },
        {
            id: 3,
            name: "Template 3",
            preview: "/templete-3.png", // Replace with your actual image paths
            description: "Minimalist Clean Template"
        }
    ];

    const tailorButton= async ()=>{
      if (!resume) return
      if(!description) {
        toast.error("enter description to proceed") 
        return
      }
      setLoading(true)
      try{
  const response = await fetch(`${API_URL}/tailor`,{
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
          setTailoredUrl(url);
        } else {
          // console.error("Invalid response data or missing PDF");
          toast.error("Somethind went wrong from server")

        }
      }catch(e:any){
        console.log(e);
        toast.error("Something went wrong, please retry later.")
        setLoading(false)
      }
    }


  useEffect(() => {
    try{
    const id = sessionStorage.getItem("id");
    if (id) setUserId(id);
    }catch(e:any){
      toast.error("Please login to proceed");
      
    }
  }, []);

  const {
    fileInputRef,
    uploading,
    uploadError,
    uploadSuccess,
    uploadedUrl,
    onUploadClick,
  } = useResumeUpload(userId)

    return (
    <div className='min-h-screen lg:h-screen lg:overflow-hidden flex flex-col md:flex-row p-6 md:p-10 gap-5'>
        <div className='order-2 md:order-1 w-full md:w-1/2 lg:w-2/5 bg-white/10 h-auto md:h-[90dvh] flex items-end justify-center gap-2 rounded-xl p-4'>
          <div className='w-full h-full flex flex-col xl:gap-16 justify-between p-3'>
            <h1 className='text-white text-sm lg:text-md xl:text-lg px-6 py-4 uppercase text-center'>Drop that dream job description here.<br/> Our AI will instantly highlight the keywords and skills you need to stand out from other applicants!</h1>
            <div className='w-full inline-flex h-full justify-center items-end gap-2  md:m-0 lg:mb-2  px-3 py-1'>
            <textarea name="job_description" rows={1} onChange={(e)=>{
              setDescription(e.target.value); 
              e.target.style.height = 'auto';
              e.target.style.height = e.target.scrollHeight + 'px';}} 
            className='bg-[#183b70] text-white w-full min-h-[4rem] max-h-[14rem] box-border block resize-none text-base text-sm md:text-md p-3 md:p-4 outline-none overflow-y-auto rounded-lg' placeholder='Enter your job description'></textarea>
            <button
                onClick={tailorButton}
                className="bg-blue-600 hover:bg-blue-800 transition w-12 h-12 md:w-16 md:h-16 text-black font-bold py-2 px-3 md:px-4 rounded-full md:rounded-4xl flex items-center justify-center focus:outline-none focus:shadow-outline"
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
                  </span>
                ) : (
                  <span className="bg-black bg-clip-text text-transparent text-center">
                    <p className='text-2xl text-white font-bold'>↑</p>
                  </span>
                )}
            </button>
            </div>
        </div>
        <input
          type="file"
          ref={fileInputRef}
          onChange={onUploadClick}
          accept=".pdf"
          style={{ display: "none" }}
        />
        </div>
        <div className='order-1 md:order-2 w-full md:w-1/2 lg:w-3/5 h-auto md:h-full flex flex-col gap-6'>
          
          { loading ? (
            <span className="flex items-center justify-center h-[inherit] text-white gap-2 flex-col mt-1/2">
              <svg
                className="animate-spin h-10 w-10 text-white"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="2"
                  fill="black"
                />
                <path
                  className="opacity-85"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                />
              </svg>
              <p>Tailoring your resume... </p>
            </span>
          ) : (
              tailoredUrl && (
                <div className="w-full h-full md:h-[90%] border rounded-md flex flex-col gap-3"
                onContextMenu={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  return false;
                }}
                style={{
                  userSelect: 'none',
                  msUserSelect: 'none'
                }}>
                  {/* Mobile-friendly PDF viewer with fallback */}
                  <iframe
                    src={`${tailoredUrl}`}
                    width="100%"
                    height="100%"
                    className="rounded-md"
                    title="Tailored Resume PDF"
                  />
                  
                  {/* Download button for mobile fallback */}
                  <a 
                    href={tailoredUrl} 
                    download="tailored_resume.pdf"
                    className="md:hidden bg-blue-600 text-white px-4 py-2 rounded-lg text-center hover:bg-blue-700 transition"
                  >
                    📥 Download Resume
                  </a>
                
                </div>
              )
              )}
          {(!tailoredUrl && !loading) &&
          <>
          <div className='flex gap-3 justify-center items-center'>
          <div className="flex items-center bg-white/10 px-5 py-3 rounded-xl shadow gap-3 w-80">
      <div className="bg-blue-600 flex items-center justify-center w-10 h-10 rounded-md">
        {/* PDF file icon (SVG) */}
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" className="w-6 h-6">
          <path strokeLinecap="round" strokeLinejoin="round" d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M14 2v6h6" />
        </svg>

      </div>
      <a href={resume? resume: ""} target='_blank' rel="noreferrer">
      <span className="text-white font-semibold text-base truncate">
        {resume ? "resume.pdf" : 'No resume selected'}
      </span>
      </a>
      {resume ? (
        <div>
        <span className="ml-auto text-green-300 px-2 py-1 rounded bg-green-900/60 text-xs">
          Recent
        </span>
        
          </div>
      ) : (
        <button
          onClick={()=>fileInputRef.current?.click()}
          className="ml-auto bg-blue-700 text-white px-4 py-1 rounded-lg hover:bg-blue-800 transition"
          type="button"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" id="Upload--Streamline-Outlined-Material" height="24" width="24">
            <path fill="#ffffff" d="M11.25 16.175V6.9l-3 3 -1.075 -1.075L12 4l4.825 4.825 -1.075 1.075 -3 -3v9.275h-1.5ZM5.5 20c-0.4 0 -0.75 -0.15 -1.05 -0.45 -0.3 -0.3 -0.45 -0.65 -0.45 -1.05v-3.575h1.5V18.5h13v-3.575h1.5V18.5c0 0.4 -0.15 0.75 -0.45 1.05 -0.3 0.3 -0.65 0.45 -1.05 0.45H5.5Z" strokeWidth="0.5"></path>
          </svg>
        </button>
      )}

    </div>
          {resume &&
          <>
          <p className='text-white hidden sm:block'>|</p>
          <button
            onClick={()=>fileInputRef.current?.click()}
            className=" size-16 bg-blue-700 text-white justify-items-center rounded-lg p-3 hover:bg-blue-800 transition  font-semibold"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" id="Upload--Streamline-Outlined-Material" height="24" width="24">
              <path fill="#ffffff" d="M11.25 16.175V6.9l-3 3 -1.075 -1.075L12 4l4.825 4.825 -1.075 1.075 -3 -3v9.275h-1.5ZM5.5 20c-0.4 0 -0.75 -0.15 -1.05 -0.45 -0.3 -0.3 -0.45 -0.65 -0.45 -1.05v-3.575h1.5V18.5h13v-3.575h1.5V18.5c0 0.4 -0.15 0.75 -0.45 1.05 -0.3 0.3 -0.65 0.45 -1.05 0.45H5.5Z" strokeWidth="0.5"></path>
            </svg>
          </button>
          </>
          }
          </div>


          <div className='w-full h-full md:h-[70vh] overflow-hidden'>
            <div className='flex gap-6 w-full h-full px-4 overflow-x-auto scrollbar-hide' style={{scrollBehavior: 'smooth'}}>
                {resumeTemplates.map((template, index) => (
                  <div 
                      key={template.id}
                      onClick={() => {if(index>0){

                        setSelectedTemplate(index)
                        console.log("pro members only");
                        toast.error("Premium users only")
                        setTimeout(()=>{
                          setSelectedTemplate(0)
                        },600)
                      }
                    }}
            className="min-w-[45%] md:min-w-[60%] lg:min-w-[45%] xl:min-w-[40%] h-full cursor-pointer relative rounded-lg overflow-hidden"
                  >
                      <img 
                          src={template.preview}
                          alt={template.name}
                          className='w-full h-full'
                      />
                      
                      {/* Color overlay when selected */}
                      {selectedTemplate === index && (
                          <div className="absolute inset-0 bg-black/70 flex items-center justify-center">
                              <div className="bg-transparent px-6 py-3 rounded-lg shadow-lg">
                                  <p className="text-white font-bold text-lg">Selected</p>
                              </div>
                          </div>
                      )}
                      
                      {/* Hover effect */}
            {selectedTemplate !== index && (
              <div className="absolute inset-0 bg-black/20 opacity-0 hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
                              <div className="bg-white/90 px-4 py-2 rounded-lg">
                                  <p className="text-black font-semibold">Click to Select</p>
                              </div>
                          </div>
                      )}
                  </div>
                ))}
            </div>
          </div>
          </>
        }
        </div>
    </div>
  )
}

export default Tailor_resume