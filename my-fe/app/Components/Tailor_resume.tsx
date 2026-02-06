"use client";
import React, { useEffect, useRef, useState } from "react";
import { useResumeUpload } from "../utiles/useUploadResume";
import toast from "react-hot-toast";
import { API_URL } from "../utiles/api";

const Tailor_resume = () => {
  const resume = sessionStorage.getItem("resume");
  const [loading, setLoading] = useState<boolean>(false);
  const [description, setDescription] = useState<string>();
  const [selectedTemplate, setSelectedTemplate] = useState<number>(0);
  const [tailoredUrl, setTailoredUrl] = useState<string | null>(null);
  const [userId, setUserId] = useState<string>("");

  const resumeTemplates = [
    { id: 0, name: "Template 0", preview: "/templete-0.png", description: "Professional Modern Template" },
    { id: 1, name: "Template 1", preview: "/templete-1.png", description: "Professional Modern Template" },
    { id: 2, name: "Template 2", preview: "/templete-2.png", description: "Creative Design Template" },
    { id: 3, name: "Template 3", preview: "/templete-3.png", description: "Minimalist Clean Template" },
  ];

  const tailorButton = async () => {
    if (!resume) return;
    if (!description) {
      toast.error("Enter a job description to proceed");
      return;
    }
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/tailor`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_desc: description, resume_url: resume, template: selectedTemplate }),
      });
      const data = await response.json();
      if (data.payload) {
        setLoading(false);
        const base64PDF = data.payload[0];
        const binary = atob(base64PDF);
        const len = binary.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) bytes[i] = binary.charCodeAt(i);
        const blob = new Blob([bytes], { type: data.media });
        const url = URL.createObjectURL(blob);
        setTailoredUrl(url);
      } else {
        toast.error("Something went wrong from server");
      }
    } catch (e: any) {
      console.log(e);
      toast.error("Something went wrong, please retry later.");
      setLoading(false);
    }
  };

  useEffect(() => {
    try {
      const id = sessionStorage.getItem("id");
      if (id) setUserId(id);
    } catch (e: any) {
      toast.error("Please login to proceed");
    }
  }, []);

  const { fileInputRef, uploading, uploadError, uploadSuccess, uploadedUrl, onUploadClick } = useResumeUpload(userId);

  return (
    <div className="min-h-screen lg:h-screen lg:overflow-hidden flex flex-col md:flex-row p-4 md:p-8 gap-5">
      {/* Left panel - Description input */}
      <div className="order-2 md:order-1 w-full md:w-1/2 lg:w-2/5 surface-card h-auto md:h-[90dvh] flex items-end justify-center gap-2 p-4">
        <div className="w-full h-full flex flex-col xl:gap-16 justify-between p-3">
          <h1 className="text-gray-300 text-sm lg:text-base px-6 py-4 uppercase text-center leading-relaxed">
            Drop that dream job description here.
            <br />
            <span className="text-emerald-400">Our AI</span> will instantly highlight the keywords and skills you need to stand out!
          </h1>
          <div className="w-full inline-flex h-full justify-center items-end gap-2 px-3 py-1">
            <textarea
              name="job_description"
              rows={1}
              onChange={(e) => {
                setDescription(e.target.value);
                e.target.style.height = "auto";
                e.target.style.height = e.target.scrollHeight + "px";
              }}
              className="input-dark w-full min-h-[4rem] max-h-[14rem] box-border block resize-none text-sm md:text-base overflow-y-auto"
              placeholder="Paste job description here..."
            />
            <button
              onClick={tailorButton}
              disabled={loading}
              className={`${loading ? "cursor-not-allowed opacity-60" : "cursor-pointer hover:bg-emerald-600"} bg-emerald-500 transition-all w-12 h-12 md:w-14 md:h-14 text-black font-bold rounded-full flex items-center justify-center`}
              type="button"
            >
              {loading ? (
                <svg className="animate-spin h-5 w-5 text-black" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 10l7-7m0 0l7 7m-7-7v18" />
                </svg>
              )}
            </button>
          </div>
        </div>
        <input type="file" ref={fileInputRef} onChange={onUploadClick} accept=".pdf" style={{ display: "none" }} />
      </div>

      {/* Right panel - Preview or Templates */}
      <div className="order-1 md:order-2 w-full md:w-1/2 lg:w-3/5 h-auto md:h-full flex flex-col gap-6">
        {loading ? (
          <span className="flex items-center justify-center h-[inherit] gap-3 flex-col mt-1/2">
            <div className="w-12 h-12 rounded-full border-2 border-emerald-500/30 border-t-emerald-500 animate-spin" />
            <p className="text-gray-400">Tailoring your resume...</p>
          </span>
        ) : (
          tailoredUrl && (
            <div
              className="w-full h-full md:h-[90%] border border-white/[0.08] rounded-xl flex flex-col gap-3 overflow-hidden"
              onContextMenu={(e) => { e.preventDefault(); e.stopPropagation(); return false; }}
              style={{ userSelect: "none", msUserSelect: "none" }}
            >
              <iframe src={`${tailoredUrl}`} width="100%" height="100%" className="rounded-xl" title="Tailored Resume PDF" />
              <a
                href={tailoredUrl}
                download="tailored_resume.pdf"
                className="md:hidden btn-primary text-center !rounded-lg mx-4 mb-4"
              >
                Download Resume
              </a>
            </div>
          )
        )}
        {!tailoredUrl && !loading && (
          <>
            {/* Resume file badge */}
            <div className="flex gap-3 justify-center items-center">
              <div className="flex items-center surface-card px-5 py-3 gap-3 w-80">
                <div className="bg-emerald-500/20 flex items-center justify-center w-10 h-10 rounded-lg">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" className="w-5 h-5 text-emerald-400">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M14 2v6h6" />
                  </svg>
                </div>
                <a href={resume ? resume : ""} target="_blank" rel="noreferrer">
                  <span className="text-white font-medium text-sm truncate hover:text-emerald-400 transition-colors">
                    {resume ? "resume.pdf" : "No resume selected"}
                  </span>
                </a>
                {resume ? (
                  <span className="ml-auto text-emerald-300 px-2 py-1 rounded-md bg-emerald-900/40 text-xs border border-emerald-500/20">Active</span>
                ) : (
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="ml-auto bg-emerald-500/20 text-emerald-400 p-2 rounded-lg hover:bg-emerald-500/30 transition"
                    type="button"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13" />
                    </svg>
                  </button>
                )}
              </div>
              {resume && (
                <>
                  <div className="w-px h-10 bg-white/[0.08] hidden sm:block" />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="w-12 h-12 bg-white/[0.05] border border-white/[0.08] text-gray-300 rounded-xl flex items-center justify-center hover:bg-white/[0.08] hover:border-white/[0.15] transition-all"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13" />
                    </svg>
                  </button>
                </>
              )}
            </div>

            {/* Template slides */}
            <div className="w-full h-full md:h-[70vh] overflow-hidden">
              <div className="flex gap-6 w-full h-full px-4 overflow-x-auto scrollbar-hide" style={{ scrollBehavior: "smooth" }}>
                {resumeTemplates.map((template, index) => (
                  <div
                    key={template.id}
                    onClick={() => setSelectedTemplate(index)}
                    className={`min-w-[45%] md:min-w-[60%] lg:min-w-[45%] xl:min-w-[40%] h-full cursor-pointer relative rounded-xl overflow-hidden border-2 transition-all duration-300 ${
                      selectedTemplate === index ? "border-emerald-500 shadow-lg shadow-emerald-500/10" : "border-white/[0.06] hover:border-white/[0.15]"
                    }`}
                  >
                    <img src={template.preview} alt={template.name} className="w-full h-full object-cover" />
                    {selectedTemplate === index && (
                      <div className="absolute inset-0 bg-black/60 flex items-center justify-center backdrop-blur-[2px]">
                        <div className="flex items-center gap-2 bg-emerald-500/20 border border-emerald-500/40 px-5 py-2.5 rounded-xl">
                          <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                          <p className="text-emerald-400 font-semibold">Selected</p>
                        </div>
                      </div>
                    )}
                    {selectedTemplate !== index && (
                      <div className="absolute inset-0 bg-black/30 opacity-0 hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
                        <div className="bg-white/10 backdrop-blur-sm border border-white/20 px-4 py-2 rounded-lg">
                          <p className="text-white font-medium text-sm">Click to Select</p>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Tailor_resume;
