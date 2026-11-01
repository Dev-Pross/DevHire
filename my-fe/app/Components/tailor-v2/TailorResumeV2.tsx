"use client";

import React, { useState } from "react";
import toast from "react-hot-toast";
import Image from "next/image";
import { API_URL } from "../../utiles/api";
import { useUser } from "../../utiles/UserContext";
import { useResumeUpload } from "../../utiles/useUploadResume";
import { UpgradePopup } from "../UpgradePopup";
import { ResumePreview0 } from "./ResumePreview0";
import { ResumePreview1 } from "./ResumePreview1";
import { ResumePreview2 } from "./ResumePreview2";
import { ResumePreview3 } from "./ResumePreview3";
import { TailorComposer, TaggedSectionItem } from "./TailorComposer";

const RESUME_TEMPLATES = [
  {
    id: 0,
    name: "Template 0",
    title: "Classic Professional",
    description: "Single-column ATS layout with horizontal dividers and clean typography",
    preview: "/templete-0.png",
  },
  {
    id: 1,
    name: "Template 1",
    title: "Modern Sidebar",
    description: "Two-column design with dynamic skill proficiency bars and colored header",
    preview: "/templete-1.png",
  },
  {
    id: 2,
    name: "Template 2",
    title: "Executive ModernCV",
    description: "Contemporary two-column layout using moderncv package styles",
    preview: "/templete-2.png",
  },
  {
    id: 3,
    name: "Template 3",
    title: "Minimalist Tech",
    description: "Clean single-column layout with boxed headers and compact margins",
    preview: "/templete-3.png",
  },
];

export const TailorResumeV2 = () => {
  const { user } = useUser();
  const resume = user?.resume_url;

  const [mode, setMode] = useState<"generate" | "revise">("generate");
  const [description, setDescription] = useState<string>("");
  const [selectedTemplate, setSelectedTemplate] = useState<number>(0);
  const [showPopup, setShowPopup] = useState(false);
  const [popupMessage, setPopupMessage] = useState("");

  // V2 Session State
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [tailoredJson, setTailoredJson] = useState<any | null>(null);
  const [revisionsRemaining, setRevisionsRemaining] = useState<number>(3);
  const [version, setVersion] = useState<number>(1);

  // Interaction State
  const [taggedItems, setTaggedItems] = useState<TaggedSectionItem[]>([]);
  const [updatedSectionKeys, setUpdatedSectionKeys] = useState<Set<string>>(new Set());

  // Loading States
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isRevising, setIsRevising] = useState<boolean>(false);
  const [isExportingPdf, setIsExportingPdf] = useState<boolean>(false);
  const [bannerMessage, setBannerMessage] = useState<string | null>(null);

  const { fileInputRef, uploading, onUploadClick } = useResumeUpload(user?.id || "");

  // -------------------------------------------------------------
  // Toggle section tag from preview hover button
  // -------------------------------------------------------------
  const handleToggleTag = (sectionKey: string, label: string) => {
    setTaggedItems((prev) => {
      const exists = prev.find((item) => item.sectionKey === sectionKey);
      if (exists) {
        return prev.filter((item) => item.sectionKey !== sectionKey);
      }
      return [...prev, { sectionKey, label, instruction: "" }];
    });
  };

  const handleRemoveTag = (sectionKey: string) => {
    setTaggedItems((prev) => prev.filter((item) => item.sectionKey !== sectionKey));
  };

  const handleInstructionChange = (sectionKey: string, instruction: string) => {
    setTaggedItems((prev) =>
      prev.map((item) =>
        item.sectionKey === sectionKey ? { ...item, instruction } : item
      )
    );
  };

  // -------------------------------------------------------------
  // STEP 1: Generate Initial Tailored Resume JSON
  // -------------------------------------------------------------
  const handleGenerate = async () => {
    if (!user?.id) {
      toast.error("Please log in to tailor your resume.");
      return;
    }
    if (!resume) {
      toast.error("Please upload a resume first.");
      fileInputRef.current?.click();
      return;
    }
    if (!description || description.trim().length < 10) {
      toast.error("Please enter a detailed job description.");
      return;
    }

    // Tier checks - all templates unlocked for free users, bounded by shared credits
    if (user?.tier === "FREE") {
      if ((user?.shared_generation_credits || 0) <= 0) {
        setPopupMessage("You have exhausted your tailoring credits. Upgrade to Pro for unlimited tailoring!");
        setShowPopup(true);
        return;
      }
    }

    setIsGenerating(true);
    try {
      const res = await fetch(`${API_URL}/tailor/v2/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user.id,
          job_desc: description,
          resume_url: resume,
          template: selectedTemplate,
          is_pro: user.tier === "PRO",
        }),
      });

      const data = await res.json();
      if (res.ok && data.success) {
        setSessionId(data.session_id);
        setTailoredJson(data.tailored_json);
        setRevisionsRemaining(data.revisions_remaining);
        setVersion(data.version);
        setMode("revise");

        // Deduct shared generation credit for FREE user on successful generation
        if (user?.tier === "FREE" && user?.id) {
          try {
            await fetch("/api/User?action=deduct_credit", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ id: user.id, type: "generation" }),
            });
            if (typeof user.shared_generation_credits === "number") {
              user.shared_generation_credits = Math.max(0, user.shared_generation_credits - 1);
            }
          } catch (creditErr) {
            console.error("Failed to deduct generation credit:", creditErr);
          }
        }

        if (data.banner_message) {
          setBannerMessage(data.banner_message);
          toast(data.banner_message, { icon: "⚠️", duration: 8000 });
        } else {
          setBannerMessage(null);
          toast.success("Resume tailored! Hover over sections to edit.");
        }
      } else {
        toast.error(data.detail || "Failed to generate tailored resume.");
      }
    } catch (err: any) {
      console.error("Generate error:", err);
      toast.error("Network error while connecting to tailoring service.");
    } finally {
      setIsGenerating(false);
    }
  };

  // -------------------------------------------------------------
  // STEP 2: Submit Tagged Section Revisions
  // -------------------------------------------------------------
  const handleRevise = async () => {
    if (!sessionId || !user?.id) return;
    if (taggedItems.length === 0) {
      toast.error("Please tag at least one section to revise.");
      return;
    }

    const empty = taggedItems.find((t) => !t.instruction.trim());
    if (empty) {
      toast.error(`Please provide revision instructions for ${empty.label}`);
      return;
    }

    setIsRevising(true);
    try {
      const res = await fetch(`${API_URL}/tailor/v2/revise`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user.id,
          session_id: sessionId,
          is_pro: user.tier === "PRO",
          comments: taggedItems.map((item) => ({
            section_key: item.sectionKey,
            instruction: item.instruction,
          })),
        }),
      });

      const data = await res.json();
      if (res.ok && data.success) {
        setRevisionsRemaining(data.revisions_remaining);
        setVersion(data.version);

        const updatedKeys = new Set(Object.keys(data.updated_sections || {}));
        setUpdatedSectionKeys(updatedKeys);

        // Instantly sync tailored_json from revision response or fallback to session
        if (data.tailored_json) {
          setTailoredJson(data.tailored_json);
        } else {
          const sessRes = await fetch(
            `${API_URL}/tailor/v2/session?user_id=${user.id}&session_id=${sessionId}&t=${Date.now()}`
          );
          if (sessRes.ok) {
            const sessData = await sessRes.json();
            if (sessData.tailored_json) {
              setTailoredJson(sessData.tailored_json);
            }
          }
        }

        setTaggedItems([]);
        toast.success("Sections updated successfully!");
        setTimeout(() => setUpdatedSectionKeys(new Set()), 3500);
      } else if (res.status === 409) {
        toast.error("A revision is already in progress. Please wait a moment.");
      } else if (res.status === 429) {
        toast.error(data.detail || "Our AI services are receiving constant pressure. Upgrade to Pro for high-speed dedicated AI.", { duration: 6000 });
      } else {
        toast.error(data.detail || "Failed to update sections.");
      }
    } catch (err: any) {
      console.error("Revise error:", err);
      toast.error("Failed to submit revision.");
    } finally {
      setIsRevising(false);
    }
  };

  // -------------------------------------------------------------
  // STEP 3: Export PDF (Option 1: Primary LaTeX Compilation)
  // -------------------------------------------------------------
  const handleExportLatexPdf = async () => {
    if (!user?.id) return;
    setIsExportingPdf(true);
    try {
      const res = await fetch(`${API_URL}/tailor/v2/export/pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user.id,
          session_id: sessionId,
          tailored_json: tailoredJson,
          template: selectedTemplate,
        }),
      });

      const data = await res.json();
      if (res.ok && data.payload && data.payload.length > 0) {
        const base64PDF = data.payload[0];
        const binary = atob(base64PDF);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
        const blob = new Blob([bytes], { type: "application/pdf" });
        const url = URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = `${tailoredJson?.static_profile?.fullname || "Resume"}_Tailored.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        toast.success("Resume downloaded successfully!");
        return;
      }

      // Automatic fallback if compile returned non-200 or empty payload
      console.warn("LaTeX compilation failed, automatically falling back to print...");
      toast("LaTeX compiler busy. Automatically opening print fallback...", { icon: "ℹ️" });
      window.print();
    } catch (err: any) {
      console.error("Export error, triggering auto fallback:", err);
      toast("LaTeX service unreachable. Automatically opening print fallback...", { icon: "ℹ️" });
      window.print();
    } finally {
      setIsExportingPdf(false);
    }
  };

  const handleRegenerate = () => {
    setMode("generate");
    setSessionId(null);
    setTailoredJson(null);
    setTaggedItems([]);
    setRevisionsRemaining(3);
  };

  const taggedKeysSet = new Set(taggedItems.map((item) => item.sectionKey));

  return (
    <div className="h-full w-full flex flex-col md:flex-row p-3 md:p-6 gap-5 bg-[#0A0A0A] min-h-0">
      <UpgradePopup isOpen={showPopup} onClose={() => setShowPopup(false)} message={popupMessage} />

      {/* Floating generation credits badge for FREE tier */}
      {user?.tier === "FREE" && (
        <div className="fixed bottom-6 right-6 bg-[#1A1A1A] border border-white/[0.08] text-gray-300 text-xs px-4 py-2 rounded-full font-medium z-50 shadow-2xl flex items-center gap-2 print:hidden backdrop-blur-md">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
          Credits: {user?.shared_generation_credits ?? 0}/5
        </div>
      )}

      {/* Hidden file input for uploading master resume */}
      <input type="file" ref={fileInputRef} onChange={onUploadClick} accept=".pdf" className="hidden" />

      {/* Left Column: Dual-Mode Composer Panel */}
      <div className="w-full md:w-1/2 lg:w-2/5 h-full flex flex-col min-h-0 shrink-0 print:hidden">
        <TailorComposer
          mode={mode}
          jobDescription={description}
          onJobDescriptionChange={setDescription}
          onGenerate={handleGenerate}
          isGenerating={isGenerating}
          taggedItems={taggedItems}
          onRemoveTag={handleRemoveTag}
          onInstructionChange={handleInstructionChange}
          onRevise={handleRevise}
          isRevising={isRevising}
          revisionsRemaining={revisionsRemaining}
          onRegenerate={handleRegenerate}
          onExportLatexPdf={handleExportLatexPdf}
          isExportingPdf={isExportingPdf}
          masterResumeUrl={resume}
        />
      </div>

      {/* Right Column: Template Selection Gallery OR Live Resume Preview */}
      <div className="w-full md:w-1/2 lg:w-3/5 h-full surface-card flex flex-col min-h-0 overflow-hidden rounded-xl">
        {mode === "generate" && !tailoredJson ? (
          // BEFORE GENERATION: TEMPLATE SELECTION GALLERY
          <div className="h-full flex flex-col p-4 sm:p-6 min-h-0">
            {/* Top Toolbar: Template Header + Resume File Status */}
            <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-white/[0.08] shrink-0">
              <div>
                <h3 className="text-gray-200 font-semibold text-sm sm:text-base">
                  Choose Resume Template
                </h3>
                <p className="text-xs text-gray-400">
                  Select a styling theme for your tailored resume
                </p>
              </div>

              {/* Active Base Resume File Badge */}
              <div className="flex items-center gap-2 bg-white/[0.04] border border-white/[0.08] px-3 py-1.5 rounded-lg text-xs">
                <span className={`w-2 h-2 rounded-full ${resume ? "bg-emerald-500" : "bg-amber-400 animate-pulse"}`} />
                {resume ? (
                  <a
                    href={resume}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gray-300 hover:text-emerald-400 font-medium truncate max-w-[150px] flex items-center gap-1 hover:underline transition-colors"
                    title="Open master resume in new tab"
                  >
                    <span>Master Resume</span>
                    <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                ) : (
                  <span className="text-gray-400 font-medium truncate max-w-[140px]">
                    No Resume Uploaded
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  title={uploading ? "Uploading..." : "Upload new master resume"}
                  className="p-1 rounded-md hover:bg-white/[0.08] text-emerald-400 hover:text-emerald-300 transition-all cursor-pointer flex items-center justify-center"
                >
                  {uploading ? (
                    <svg className="animate-spin h-3.5 w-3.5 text-amber-400" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                    </svg>
                  ) : (
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth={2}
                      stroke="currentColor"
                      className="w-3.5 h-3.5"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13"
                      />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {/* Template Cards Grid */}
            <div className="flex-1 min-h-0 overflow-y-auto py-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pb-2">
                {RESUME_TEMPLATES.map((tmpl) => {
                  const isSelected = selectedTemplate === tmpl.id;
                  return (
                    <div
                      key={tmpl.id}
                      onClick={() => setSelectedTemplate(tmpl.id)}
                      className={`group relative rounded-xl border-2 transition-all duration-200 p-2.5 flex flex-col cursor-pointer bg-white/[0.02] hover:bg-white/[0.04] ${isSelected
                          ? "border-emerald-500 shadow-lg shadow-emerald-500/10 ring-1 ring-emerald-500/30"
                          : "border-white/[0.08] hover:border-white/[0.2]"
                        }`}
                    >
                      {/* Thumbnail Container */}
                      <div className="w-full h-44 sm:h-48 rounded-lg overflow-hidden relative bg-black/40 border border-white/[0.04]">
                        <img
                          src={tmpl.preview}
                          alt={tmpl.name}
                          className="w-full h-full object-cover object-top transition-transform duration-300 group-hover:scale-105"
                        />
                        {isSelected && (
                          <div className="absolute top-2 right-2 bg-emerald-500 text-black text-[11px] font-bold px-2.5 py-0.5 rounded-full shadow-md flex items-center gap-1">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                            <span>Selected</span>
                          </div>
                        )}
                      </div>

                      {/* Title & Description */}
                      <div className="mt-2.5 flex flex-col gap-0.5">
                        <div className="flex items-center justify-between">
                          <span className={`text-xs font-bold ${isSelected ? "text-emerald-400" : "text-gray-200"}`}>
                            {tmpl.title}
                          </span>
                          <span className="text-[10px] text-gray-500 uppercase font-mono">
                            {tmpl.name}
                          </span>
                        </div>
                        <p className="text-[11px] text-gray-400 line-clamp-2 leading-relaxed">
                          {tmpl.description}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ) : (
          // AFTER GENERATION: LIVE PREVIEW WITH SECTION EDITING
          <div className="h-full flex flex-col min-h-0">
            {/* Pressure / Rate Limit Fallback Banner */}
            {bannerMessage && (
              <div className="bg-amber-500/10 border-b border-amber-500/30 px-4 py-2.5 flex items-center justify-between text-xs text-amber-200 print:hidden shrink-0">
                <div className="flex items-center gap-2">
                  <span className="bg-amber-500/20 text-amber-400 font-bold px-1.5 py-0.5 rounded text-[10px] uppercase tracking-wider border border-amber-500/30">
                    High AI Load
                  </span>
                  <span>{bannerMessage}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setBannerMessage(null)}
                  className="text-amber-400/80 hover:text-amber-200 ml-3 text-base leading-none p-1 cursor-pointer"
                  title="Dismiss notice"
                >
                  ✕
                </button>
              </div>
            )}

            {/* Top Toolbar with Template Switcher */}
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/[0.08] bg-white/[0.02] shrink-0 print:hidden">
              <div className="flex items-center gap-2 overflow-x-auto">
                <span className="text-xs text-gray-400 font-medium hidden sm:inline">
                  Template:
                </span>
                {RESUME_TEMPLATES.map((tmpl) => (
                  <button
                    key={tmpl.id}
                    type="button"
                    onClick={() => {
                      setSelectedTemplate(tmpl.id);
                    }}
                    className={`px-2.5 py-1 text-xs rounded-lg font-medium transition-all cursor-pointer ${selectedTemplate === tmpl.id
                        ? "bg-emerald-500 text-black font-semibold shadow-sm"
                        : "bg-white/[0.05] text-gray-300 hover:bg-white/[0.1] hover:text-white"
                      }`}
                  >
                    {tmpl.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Scrollable Live Resume Canvas */}
            <div className="flex-1 min-h-0 overflow-y-auto p-2 sm:p-4">
              {selectedTemplate === 1 ? (
                <ResumePreview1
                  data={tailoredJson}
                  taggedSectionKeys={taggedKeysSet}
                  updatedSectionKeys={updatedSectionKeys}
                  onToggleTag={handleToggleTag}
                />
              ) : selectedTemplate === 2 ? (
                <ResumePreview2
                  data={tailoredJson}
                  taggedSectionKeys={taggedKeysSet}
                  updatedSectionKeys={updatedSectionKeys}
                  onToggleTag={handleToggleTag}
                />
              ) : selectedTemplate === 3 ? (
                <ResumePreview3
                  data={tailoredJson}
                  taggedSectionKeys={taggedKeysSet}
                  updatedSectionKeys={updatedSectionKeys}
                  onToggleTag={handleToggleTag}
                />
              ) : (
                <ResumePreview0
                  data={tailoredJson}
                  taggedSectionKeys={taggedKeysSet}
                  updatedSectionKeys={updatedSectionKeys}
                  onToggleTag={handleToggleTag}
                />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
