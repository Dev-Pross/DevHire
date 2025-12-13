"use client";
import React, { useEffect, useState } from "react";
import { useResumeUpload } from "../utiles/useUploadResume";
import toast from "react-hot-toast";
import { API_URL } from "../utiles/api";

const PortfolioPage = () => {

  const [resume, setResume] = useState<string>("");
  const [userId, setUserId] = useState<string>("");
  const { fileInputRef,onUploadClick } = useResumeUpload(userId);
  const [selectedTemplate, setSelectedTemplate] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false)
  const [code, setCode] = useState<string>("")

  const handlePortfolio = async()=>{
    setLoading(true)
    if(!resume) {
      setLoading(false)
      toast.error("Please upload resume first")
      return
    }
    try{
      const res = await fetch(`${API_URL}/portfolio`,{
        method: 'POST',
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_url: resume,
          template: selectedTemplate,
        })
      });
      
      const data = await res.json()
      if(data?.success){
        setCode(data.payload)
        setLoading(false)
      }
      else {
        setLoading(false)
        toast.error('something went wrong')
      }
    }
    catch (e){
      toast.error(e instanceof Error ? e.message: "Unknow error")
      setLoading(false)
    }
  }
  const portfolioTemplates = [
    {
      id: 0,
      name: "Template 0",
      preview: "/portfolio_1.png", // Replace with your actual image paths
      description: "Professional Modern Template",
    },
    {
      id: 1,
      name: "Template 1",
      preview: "/portfolio_2.png", // Replace with your actual image paths
      description: "Professional Modern Template",
    },
    {
      id: 2,
      name: "Template 2",
      preview: "/portfolio_3.png", // Replace with your actual image paths
      description: "Creative Design Template",
    },
    {
      id: 3,
      name: "Template 3",
      preview: "/portfolio_4.png", // Replace with your actual image paths
      description: "Minimalist Clean Template",
    },
    {
    id: 4,
      name: "Template 4",
      preview: "/portfolio_5.png", // Replace with your actual image paths
      description: "Minimalist Clean Template",
    },
  ];
  useEffect(() => {
    try {
      const id = sessionStorage.getItem("id");
      const resume = sessionStorage.getItem("resume");
      if (resume) setResume(resume)
      if (id) setUserId(id);
    } catch (e: any) {
      toast.error("Please login to proceed");
    }
  }, []);
  return (
    <>
      <div className="min-h-screen lg:h-full  flex flex-col p-6 md:p-10 gap-5">
        {/* upload button */}
        <>
        <input
          type="file"
          ref={fileInputRef}
          onChange={onUploadClick}
          accept=".pdf"
          style={{ display: "none" }}
        />
          <div className="flex gap-3 justify-center items-center">
            <div className="flex items-center bg-white/10 px-5 py-3 rounded-xl shadow gap-3 w-80">
              <div className="bg-blue-600 flex items-center justify-center w-10 h-10 rounded-md">
                {/* PDF file icon (SVG) */}
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                  className="w-6 h-6"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M14 2v6h6"
                  />
                </svg>
              </div>
              <a href={resume ? resume : ""} target="_blank" rel="noreferrer">
                <span className="text-white font-semibold text-base truncate">
                  {resume ? "resume.pdf" : "No resume selected"}
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
                  onClick={() => fileInputRef.current?.click()}
                  className="ml-auto bg-blue-700 text-white px-4 py-1 rounded-lg hover:bg-blue-800 transition"
                  type="button"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    id="Upload--Streamline-Outlined-Material"
                    height="24"
                    width="24"
                  >
                    <path
                      fill="#ffffff"
                      d="M11.25 16.175V6.9l-3 3 -1.075 -1.075L12 4l4.825 4.825 -1.075 1.075 -3 -3v9.275h-1.5ZM5.5 20c-0.4 0 -0.75 -0.15 -1.05 -0.45 -0.3 -0.3 -0.45 -0.65 -0.45 -1.05v-3.575h1.5V18.5h13v-3.575h1.5V18.5c0 0.4 -0.15 0.75 -0.45 1.05 -0.3 0.3 -0.65 0.45 -1.05 0.45H5.5Z"
                      strokeWidth="0.5"
                    ></path>
                  </svg>
                </button>
              )}
            </div>
            {resume && (
              <>
                <p className="text-white hidden sm:block">|</p>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className=" size-16 bg-blue-700 text-white justify-items-center rounded-lg p-3 hover:bg-blue-800 transition  font-semibold"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    id="Upload--Streamline-Outlined-Material"
                    height="24"
                    width="24"
                  >
                    <path
                      fill="#ffffff"
                      d="M11.25 16.175V6.9l-3 3 -1.075 -1.075L12 4l4.825 4.825 -1.075 1.075 -3 -3v9.275h-1.5ZM5.5 20c-0.4 0 -0.75 -0.15 -1.05 -0.45 -0.3 -0.3 -0.45 -0.65 -0.45 -1.05v-3.575h1.5V18.5h13v-3.575h1.5V18.5c0 0.4 -0.15 0.75 -0.45 1.05 -0.3 0.3 -0.65 0.45 -1.05 0.45H5.5Z"
                      strokeWidth="0.5"
                    ></path>
                  </svg>
                </button>
              </>
            )}
          </div>
        </>
        <div className="order-1 md:order-1 w-full bg-white/10 min-h-full md:h-[90dvh] flex flex-col gap-2 rounded-xl p-4">
          {loading ? <div className=" h-screen w-full flex justify-center items-center bg-white/10 rounded-md"><span className="flex items-center justify-center gap-2 cursor-not-allowed">
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
            Generating...</span></div> : 
            (code ? 
              (<div className='w-full h-screen  object-fill'> 
                  <iframe
                      srcDoc={code}
                      width="100%"
                      height="100%"
                      className="rounded-md"
                      title="Tailored Resume PDF"
                  />
              </div>)
            : (
          <div
            className="flex gap-6 w-full h-[90%] px-4 grid-cols-2  overflow-y-auto"
            style={{ scrollBehavior: "smooth" }}
          >
            {portfolioTemplates.map((template, index) => (
              <div
                key={template.id}
                onClick={() => {
                  setSelectedTemplate(index);
                }}
                className="min-w-full md:min-w-[50%] lg:min-w-xs h-[50dvh] md:h-full cursor-pointer relative rounded-xl overflow-hidden"
              >
                <img
                  src={template.preview}
                  alt={template.name}
                  className="w-full h-full object-fill"
                />

                {selectedTemplate === index && (
                  <div className="absolute inset-0 bg-black/70 flex items-center justify-center">
                    <div className="bg-transparent px-6 py-3 rounded-lg shadow-lg">
                      <p className="text-white font-bold text-lg">Selected</p>
                    </div>
                  </div>
                )}
                {selectedTemplate !== index && (
                  <div className="absolute inset-0 bg-black/20 opacity-0 hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
                    <div className="bg-white/90 px-4 py-2 rounded-lg">
                      <p className="text-black font-semibold">
                        Click to Select
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
          ))}

          
          <div className="w-full h-16 flex justify-center items-center gap-4">
            {code ? (
              <>
                <button
                  onClick={() => {
                    const blob = new Blob([code], { type: "text/html" });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = "portfolio.html";
                    a.click();
                    URL.revokeObjectURL(url);
                  }}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg text-center hover:bg-green-700 transition flex items-center gap-2"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={2}
                    stroke="currentColor"
                    className="w-5 h-5"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                    />
                  </svg>
                  Download Portfolio
                </button>
                <button
                  onClick={() => setCode("")}
                  className="bg-gray-600 text-white px-4 py-2 rounded-lg text-center hover:bg-gray-700 transition"
                >
                  Generate New
                </button>
              </>
            ) : (
              <button
                onClick={handlePortfolio}
                disabled={loading}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg text-center place-self-center hover:bg-blue-700 transition"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2 cursor-not-allowed">
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
                    Generating Portfolio...
                  </span>
                ) : (
                  "Generate Portfolio"
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default PortfolioPage;
