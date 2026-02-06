"use client";
import React, { useEffect, useState } from "react";
import { useResumeUpload } from "../utiles/useUploadResume";
import toast from "react-hot-toast";
import { API_URL } from "../utiles/api";

const PortfolioPage = () => {
  const [resume, setResume] = useState<string>("");
  const [userId, setUserId] = useState<string>("");
  const { fileInputRef, onUploadClick } = useResumeUpload(userId);
  const [selectedTemplate, setSelectedTemplate] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [code, setCode] = useState<string>("");

  const handlePortfolio = async () => {
    setLoading(true);
    if (!resume) {
      setLoading(false);
      toast.error("Please upload resume first");
      return;
    }
    try {
      const res = await fetch(`${API_URL}/portfolio`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_url: resume, template: selectedTemplate }),
      });
      const data = await res.json();
      if (data?.success) {
        setCode(data.payload);
        setLoading(false);
      } else {
        setLoading(false);
        toast.error("Something went wrong");
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Unknown error");
      setLoading(false);
    }
  };

  const portfolioTemplates = [
    { id: 0, name: "Template 0", preview: "/portfolio_1.png", description: "Professional Modern Template" },
    { id: 1, name: "Template 1", preview: "/portfolio_2.png", description: "Professional Modern Template" },
    { id: 2, name: "Template 2", preview: "/portfolio_3.png", description: "Creative Design Template" },
    { id: 3, name: "Template 3", preview: "/portfolio_4.png", description: "Minimalist Clean Template" },
    { id: 4, name: "Template 4", preview: "/portfolio_5.png", description: "Minimalist Clean Template" },
  ];

  useEffect(() => {
    try {
      const id = sessionStorage.getItem("id");
      const resume = sessionStorage.getItem("resume");
      if (resume) setResume(resume);
      if (id) setUserId(id);
    } catch (e: any) {
      toast.error("Please login to proceed");
    }
  }, []);

  return (
    <div className="min-h-screen lg:h-full flex flex-col p-4 md:p-8 gap-5">
      {/* Upload section */}
      <input type="file" ref={fileInputRef} onChange={onUploadClick} accept=".pdf" style={{ display: "none" }} />
      <div className="flex gap-3 justify-center items-center">
        <div className="flex items-center surface-card px-5 py-3 gap-3 w-full max-w-80">
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

      {/* Main content area */}
      <div className="w-full surface-card min-h-full md:h-[90dvh] flex flex-col gap-2 p-4">
        {loading ? (
          <div className="h-screen w-full flex justify-center items-center">
            <div className="flex flex-col items-center gap-3">
              <div className="w-12 h-12 rounded-full border-2 border-emerald-500/30 border-t-emerald-500 animate-spin" />
              <span className="text-gray-400 text-sm">Generating portfolio...</span>
            </div>
          </div>
        ) : code ? (
          <div className="w-full h-screen object-fill">
            <iframe srcDoc={code} width="100%" height="100%" className="rounded-xl border border-white/[0.06]" title="Generated Portfolio" />
          </div>
        ) : (
          <div className="flex gap-6 w-full h-[90%] px-4 overflow-x-auto overflow-y-hidden" style={{ scrollBehavior: "smooth" }}>
            {portfolioTemplates.map((template, index) => (
              <div
                key={template.id}
                onClick={() => setSelectedTemplate(index)}
                className={`min-w-full md:min-w-[50%] lg:min-w-xs h-[50dvh] md:h-full cursor-pointer relative rounded-xl overflow-hidden border-2 transition-all duration-300 ${
                  selectedTemplate === index ? "border-emerald-500 shadow-lg shadow-emerald-500/10" : "border-white/[0.06] hover:border-white/[0.15]"
                }`}
              >
                <img src={template.preview} alt={template.name} className="w-full h-full object-fill" />
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
        )}

        {/* Action buttons */}
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
                className="btn-primary !px-6 flex items-center gap-2"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                </svg>
                Download Portfolio
              </button>
              <button
                onClick={() => setCode("")}
                className="btn-secondary !px-6"
              >
                Generate New
              </button>
            </>
          ) : (
            <button
              onClick={handlePortfolio}
              disabled={loading}
              className="btn-primary !px-8 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                  </svg>
                  Generating...
                </span>
              ) : (
                "Generate Portfolio"
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default PortfolioPage;
