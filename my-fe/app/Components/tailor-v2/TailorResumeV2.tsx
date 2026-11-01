"use client";

import React, { useState } from "react";
import toast from "react-hot-toast";
import { API_URL } from "../../utiles/api";
import { useUser } from "../../utiles/UserContext";
import { useResumeUpload } from "../../utiles/useUploadResume";
import { UpgradePopup } from "../UpgradePopup";
import { ResumePreview0 } from "./ResumePreview0";
import { ResumePreview1 } from "./ResumePreview1";
import { ResumePreview2 } from "./ResumePreview2";
import { ResumePreview3 } from "./ResumePreview3";
import { TailorStudioV2Split, TaggedSectionItem, ChatMessage } from "./TailorStudioV2Split";

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

const QUICK_PROMPTS = [
  "re rank for gen ai RAG first based order",
  "Make bullet points punchier with metrics",
  "Emphasize distributed systems & Kafka throughput",
  "Tailor skills and summary to match this JD strictly",
];

const SAMPLE_TAILORED_RESUME: any = {
  static_profile: {
    fullname: "Alex Morgan",
    email: { text: "alex.morgan@email.com", href: "mailto:alex.morgan@email.com" },
    phone: "+1 (555) 019-2834",
    location: "San Francisco, CA",
    linkedin: { text: "LinkedIn", href: "https://linkedin.com/in/alexmorgan" },
    github: { text: "GitHub", href: "https://github.com/alexmorgan" },
  },
  summary: "Results-driven Senior Full Stack and AI Systems Engineer with 6+ years architecting high-throughput distributed microservices and LLM-powered RAG pipelines in production environments.",
  skills: [
    { category: "Languages", skills: ["TypeScript", "Python", "Go", "SQL", "Rust"] },
    { category: "Frameworks and AI", skills: ["Next.js", "React", "FastAPI", "PyTorch", "LangChain", "Node.js"] },
    { category: "Cloud and Data", skills: ["AWS", "Docker", "Kubernetes", "PostgreSQL", "Redis", "Kafka"] },
  ],
  experience: [
    {
      company: "Apex Neural Systems",
      role: "Lead Full Stack and AI Systems Engineer",
      location: "San Francisco, CA",
      date: "2023 - Present",
      bullets: [
        "Architected distributed RAG knowledge retrieval pipeline indexing 400M+ enterprise documents with sub-60ms vector search latency.",
        "Engineered real-time streaming WebSocket infrastructure serving 85k concurrent active sessions across Next.js and FastAPI backends.",
        "Spearheaded migration to micro-frontend architecture, accelerating CI/CD build speeds by 42% and eliminating deployment downtime."
      ]
    },
    {
      company: "DataSphere Technologies",
      role: "Senior Software Engineer",
      location: "Austin, TX",
      date: "2021 - 2023",
      bullets: [
        "Developed high-volume transactional microservices processing 12,000 requests/sec with 99.99% availability.",
        "Optimized PostgreSQL queries and Redis caching layers, reducing p99 database response times by 68%."
      ]
    }
  ],
  projects: [
    {
      name: "DevHire Autonomous Job Engine",
      role: "Lead Architect",
      date: "2024",
      bullets: [
        "Built automated multi-agent job application engine with real-time DOM interception and automated ATS credential matching.",
        "Integrated dynamic one-page LaTeX resume generation engine with LaTeX compiler fallback and vector re-ranking."
      ]
    },
    {
      name: "VectorStream LLM Gateway",
      role: "Core Contributor",
      date: "2023",
      bullets: [
        "Engineered fault-tolerant multi-provider LLM gateway featuring automatic failover, semantic caching, and token budgeting."
      ]
    }
  ],
  education: [
    {
      degree: "B.S. in Computer Science and Applied Mathematics",
      institution: "University of California, Berkeley",
      location: "Berkeley, CA",
      date: "2017 - 2021",
      gpa: "3.9 / 4.0"
    }
  ]
};

export const TailorResumeV2 = () => {
  const { user } = useUser();
  const resume = user?.resume_url;

  const [mode, setMode] = useState<"generate" | "revise">("generate");
  const [description, setDescription] = useState<string>("");
  const [selectedTemplate, setSelectedTemplate] = useState<number>(0);
  const [showPopup, setShowPopup] = useState(false);
  const [popupMessage, setPopupMessage] = useState("");

  const [inspectingTemplate, setInspectingTemplate] = useState<number | null>(null);
  const [mobileStudioTab, setMobileStudioTab] = useState<"resume" | "chat">("resume");

  // V2 Session State
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [tailoredJson, setTailoredJson] = useState<any | null>(null);
  const [revisionsRemaining, setRevisionsRemaining] = useState<number>(3);
  const [version, setVersion] = useState<number>(1);
  const [bannerMessage, setBannerMessage] = useState<string | null>(null);

  // Tagged Section Items & Keys
  const [taggedItems, setTaggedItems] = useState<TaggedSectionItem[]>([]);
  const [updatedSectionKeys, setUpdatedSectionKeys] = useState<Set<string>>(new Set());

  // Conversational Chat History
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);

  // Loading States
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isRevising, setIsRevising] = useState<boolean>(false);
  const [isExportingPdf, setIsExportingPdf] = useState<boolean>(false);

  // Upload Hook
  const { fileInputRef, uploading, onUploadClick } = useResumeUpload(user?.id || "");

  // -------------------------------------------------------------
  // Toggle section tag from preview hover / click button
  // -------------------------------------------------------------
  const handleToggleTag = (sectionKey: string, label: string) => {
    const isAlreadyTagged = taggedItems.some((item) => item.sectionKey === sectionKey);
    if (isAlreadyTagged) {
      setTaggedItems((prev) => prev.filter((item) => item.sectionKey !== sectionKey));
      toast(`Removed tag: ${label}`, { duration: 1500 });
    } else {
      setTaggedItems((prev) => [...prev, { sectionKey, label, instruction: "" }]);
      toast.success(`Tagged: ${label} for revision`, { duration: 1800 });
    }
  };

  const handleRemoveTag = (sectionKey: string) => {
    setTaggedItems((prev) => prev.filter((item) => item.sectionKey !== sectionKey));
  };

  // -------------------------------------------------------------
  // STEP 1: Generate Initial Tailored Resume
  // -------------------------------------------------------------
  const handleGenerate = async () => {
    if (!resume) {
      toast.error("Please upload a resume first.");
      fileInputRef.current?.click();
      return;
    }
    if (!description || description.trim().length < 10) {
      toast.error("Please enter a detailed job description.");
      return;
    }

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

        // Seed initial chatbot message
        setChatMessages([
          {
            id: "msg_welcome",
            sender: "ai",
            text: "Your resume has been tailored for the target Job Description! Tap or click any section on the preview to tag it for instant revision, or prompt below.",
            timestamp: "Just now",
            version: 1,
          },
        ]);

        if (user?.tier === "FREE" && user?.id) {
          try {
            await fetch("/api/User?action=deduct_credit", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ userId: user.id }),
            });
          } catch (e) {
            console.error("Failed to deduct shared credit:", e);
          }
        }

        if (data.banner_message) {
          setBannerMessage(data.banner_message);
          toast(data.banner_message, { duration: 8000 });
        } else {
          setBannerMessage(null);
          toast.success("Resume tailored! Tag sections to edit or re-rank.");
        }
      } else {
        toast.error(data.detail || "Failed to generate tailored resume.");
      }
    } catch (err: any) {
      console.error("Tailor generate error:", err);
      toast.error("Network error while connecting to tailoring service.");
    } finally {
      setIsGenerating(false);
    }
  };

  // -------------------------------------------------------------
  // STEP 2: Submit Revisions via Unified Prompt Bar or Composer
  // -------------------------------------------------------------
  const executeRevision = async (itemsToRevise: TaggedSectionItem[], userPromptText?: string) => {
    if (!sessionId || !user?.id) return;
    if (itemsToRevise.length === 0) {
      toast.error("Please tag at least one section to revise.");
      return;
    }

    const payloadComments = itemsToRevise.map((item) => ({
      section_key: item.sectionKey,
      instruction: (item.instruction || userPromptText || "Optimize and re-rank this section to strictly match the JD").trim(),
    }));

    setIsRevising(true);

    // Append user message to chat stream
    const taggedLabels = itemsToRevise.map((t) => t.label);
    const userPromptDisplay = userPromptText || itemsToRevise.map((t) => `${t.label}: ${t.instruction}`).join(" | ");
    setChatMessages((prev) => [
      ...prev,
      {
        id: `user_${Date.now()}`,
        sender: "user",
        text: userPromptDisplay,
        timestamp: "Just now",
        taggedSections: taggedLabels,
      },
    ]);

    try {
      const res = await fetch(`${API_URL}/tailor/v2/revise`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user.id,
          session_id: sessionId,
          is_pro: user.tier === "PRO",
          comments: payloadComments,
        }),
      });

      const data = await res.json();
      if (res.ok && data.success) {
        setRevisionsRemaining(data.revisions_remaining);
        const newVer = data.version || version + 1;
        setVersion(newVer);

        const updatedKeys = new Set(Object.keys(data.updated_sections || {}));
        setUpdatedSectionKeys(updatedKeys);

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

        // Append AI response to chat stream
        setChatMessages((prev) => [
          ...prev,
          {
            id: `ai_${Date.now()}`,
            sender: "ai",
            text: `Successfully updated ${taggedLabels.join(", ")}. Factual anchors preserved.`,
            timestamp: "Just now",
            version: newVer,
          },
        ]);

        setTaggedItems([]);
        toast.success("Sections updated successfully!");
        setTimeout(() => setUpdatedSectionKeys(new Set()), 3500);
      } else if (res.status === 409) {
        toast.error("A revision is already in progress. Please wait a moment.");
      } else if (res.status === 429) {
        toast.error(data.detail || "Quota reached. Upgrade to Pro for unlimited AI tailoring.", { duration: 6000 });
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

  const handleReviseWithPrompt = (userPromptText: string) => {
    let items = [...taggedItems];
    if (items.length === 0) {
      // Default to "projects" if prompt mentions projects or re-rank
      if (userPromptText.toLowerCase().includes("project") || userPromptText.toLowerCase().includes("re rank") || userPromptText.toLowerCase().includes("rerank")) {
        items = [{ sectionKey: "projects", label: "Projects", instruction: userPromptText }];
      } else if (userPromptText.toLowerCase().includes("skill")) {
        items = [{ sectionKey: "skills", label: "Skills", instruction: userPromptText }];
      } else if (userPromptText.toLowerCase().includes("summary")) {
        items = [{ sectionKey: "summary", label: "Summary", instruction: userPromptText }];
      } else if (
        userPromptText.toLowerCase().includes("city") ||
        userPromptText.toLowerCase().includes("location") ||
        userPromptText.toLowerCase().includes("header") ||
        userPromptText.toLowerCase().includes("phone") ||
        userPromptText.toLowerCase().includes("contact")
      ) {
        items = [{ sectionKey: "header", label: "Header & Contact", instruction: userPromptText }];
      } else {
        toast.error("Please tag a section on the resume preview first.");
        return;
      }
    }
    executeRevision(items, userPromptText);
  };

  // -------------------------------------------------------------
  // STEP 3: Export PDF (Primary LaTeX with fallback)
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
        a.download = `DevHire_Tailored_Resume_T${selectedTemplate}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success("LaTeX PDF exported successfully!");
        return;
      }

      console.warn("LaTeX compilation failed, falling back to print...");
      toast("LaTeX compiler busy. Opening print fallback...");
      window.print();
    } catch (err: any) {
      console.error("Export error, triggering auto fallback:", err);
      toast("Opening print fallback...");
      window.print();
    } finally {
      setIsExportingPdf(false);
    }
  };

  const handleStartOver = () => {
    setMode("generate");
    setSessionId(null);
    setTailoredJson(null);
    setTaggedItems([]);
    setRevisionsRemaining(3);
    setChatMessages([]);
  };

  const handleLoadSampleData = () => {
    setSessionId("demo_session_sample");
    setTailoredJson(SAMPLE_TAILORED_RESUME);
    setRevisionsRemaining(3);
    setVersion(1);
    setMode("revise");
    setChatMessages([
      {
        id: "msg_welcome",
        sender: "ai",
        text: "Studio Demo active! You are previewing with sample candidate data. Tap any section on the preview to tag it, or prompt revisions below.",
        timestamp: "Just now",
        version: 1,
      },
    ]);
    toast.success("Studio Demo Loaded! Ready to revise and preview.", { duration: 4000 });
  };

  const taggedKeysSet = new Set(taggedItems.map((item) => item.sectionKey));

  // Render the Selected Resume Preview Component
  const renderResumePreview = () => {
    const props = {
      data: tailoredJson,
      taggedSectionKeys: taggedKeysSet,
      updatedSectionKeys: updatedSectionKeys,
      onToggleTag: handleToggleTag,
    };

    if (selectedTemplate === 1) return <ResumePreview1 {...props} />;
    if (selectedTemplate === 2) return <ResumePreview2 {...props} />;
    if (selectedTemplate === 3) return <ResumePreview3 {...props} />;
    return <ResumePreview0 {...props} />;
  };

  return (
    <div className="h-full w-full flex flex-col bg-[#0A0A0A] overflow-hidden relative">
      <UpgradePopup isOpen={showPopup} onClose={() => setShowPopup(false)} message={popupMessage} />

      {/* ========================================================= */}
      {/* HIGH-RES TEMPLATE INSPECTOR LIGHTBOX MODAL               */}
      {/* ========================================================= */}
      {inspectingTemplate !== null && (
        <div
          className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-6"
          onClick={() => setInspectingTemplate(null)}
        >
          <div
            className="surface-card border border-white/[0.15] rounded-2xl max-w-xl w-full max-h-[92vh] flex flex-col overflow-hidden shadow-2xl relative"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="px-4 py-3 border-b border-white/[0.08] flex items-center justify-between shrink-0 bg-[#161616]">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-white font-bold text-sm sm:text-base">
                    {RESUME_TEMPLATES[inspectingTemplate].title}
                  </h3>
                  <span className="text-[11px] bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 px-2 py-0.5 rounded font-mono font-semibold">
                    T{RESUME_TEMPLATES[inspectingTemplate].id}
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-0.5">
                  {RESUME_TEMPLATES[inspectingTemplate].description}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setInspectingTemplate(null)}
                className="w-8 h-8 rounded-full bg-white/[0.06] hover:bg-white/[0.12] text-gray-300 hover:text-white flex items-center justify-center text-sm transition cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Modal Image Body (Scrollable High-Res View) */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 flex flex-col items-center justify-start bg-black/40">
              <div className="w-full max-w-md bg-white rounded-lg shadow-2xl overflow-hidden border border-white/[0.1]">
                <img
                  src={RESUME_TEMPLATES[inspectingTemplate].preview}
                  alt={RESUME_TEMPLATES[inspectingTemplate].name}
                  className="w-full h-full object-contain block"
                />
              </div>
            </div>

            {/* Modal Footer Actions */}
            <div className="px-4 py-3 border-t border-white/[0.08] flex items-center justify-between gap-3 shrink-0 bg-[#161616]">
              <button
                type="button"
                onClick={() => setInspectingTemplate(null)}
                className="px-3.5 py-1.5 text-xs text-gray-400 hover:text-white rounded-lg hover:bg-white/[0.06] transition"
              >
                Back
              </button>

              <button
                type="button"
                onClick={() => {
                  setSelectedTemplate(inspectingTemplate);
                  setInspectingTemplate(null);
                  toast.success(`Selected ${RESUME_TEMPLATES[inspectingTemplate].title}!`);
                }}
                className="px-4 py-2 text-xs bg-emerald-500 text-black hover:bg-emerald-400 font-bold rounded-lg transition shadow-md shadow-emerald-500/20 flex items-center gap-1.5 cursor-pointer"
              >
                <span>✓ Select This Template (T{RESUME_TEMPLATES[inspectingTemplate].id})</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating generation credits badge for FREE tier */}
      {user?.tier === "FREE" && (
        <div className="fixed bottom-4 right-4 bg-[#1A1A1A]/90 border border-white/[0.08] text-gray-300 text-xs px-3 py-1.5 rounded-full font-medium z-50 shadow-2xl flex items-center gap-2 print:hidden backdrop-blur-md">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Credits: {user?.shared_generation_credits ?? 0}/5</span>
        </div>
      )}

      {/* Hidden file input for uploading master resume */}
      <input type="file" ref={fileInputRef} onChange={onUploadClick} accept=".pdf" className="hidden" />

      {/* ========================================================= */}
      {/* TOP MASTER CONTROL BAR (CLEAN & ADAPTIVE)                 */}
      {/* ========================================================= */}
      <div className="px-3 sm:px-6 py-2 bg-[#121212] border-b border-white/[0.08] flex items-center justify-between gap-2 shrink-0 z-30">
        {tailoredJson ? (
          <>
            {/* Template quick pills on left */}
            <div className="flex items-center gap-1 bg-white/[0.03] p-0.5 sm:p-1 rounded-xl border border-white/[0.08]">
              {RESUME_TEMPLATES.map((tmpl) => (
                <button
                  key={tmpl.id}
                  type="button"
                  onClick={() => setSelectedTemplate(tmpl.id)}
                  className={`px-2 sm:px-2.5 py-0.5 text-xs rounded-md transition font-medium cursor-pointer ${
                    selectedTemplate === tmpl.id
                      ? "bg-white/[0.15] text-emerald-300 font-semibold"
                      : "text-gray-400 hover:text-white"
                  }`}
                >
                  T{tmpl.id}
                </button>
              ))}
            </div>

            {/* Action Controls on right */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleStartOver}
                className="text-xs text-gray-400 hover:text-white px-2.5 py-1 rounded-lg hover:bg-white/[0.06] transition whitespace-nowrap cursor-pointer"
              >
                Start Over
              </button>

              <button
                type="button"
                onClick={handleExportLatexPdf}
                disabled={isExportingPdf}
                className="text-xs bg-emerald-500 text-black hover:bg-emerald-400 font-semibold px-3 py-1.5 rounded-lg transition flex items-center gap-1 shadow-sm whitespace-nowrap cursor-pointer"
              >
                {isExportingPdf ? "Compiling..." : "Download PDF ↓"}
              </button>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-between w-full">
            <span className="text-xs font-semibold text-gray-300">Tailor Resume Studio</span>
          </div>
        )}
      </div>

      {/* ========================================================= */}
      {/* PHASE 1: BEFORE GENERATION                               */}
      {/* ========================================================= */}
      {mode === "generate" && !tailoredJson ? (
        <div className="flex-1 w-full flex flex-col md:flex-row min-h-0 overflow-hidden">

          {/* ---- LEFT COLUMN: Master Resume (top) + Template Strip + JD Input ---- */}
          <div className="w-full md:w-1/2 lg:w-2/5 flex flex-col h-full p-3 sm:p-6 gap-3.5 overflow-y-auto pb-10">

            {/* 1. Master Resume Status Card (TOP OF COLUMN) */}
            <div className="flex items-center justify-between bg-white/[0.03] border border-white/[0.08] px-3.5 py-2.5 rounded-xl shrink-0 gap-2.5">
              <div className="flex items-center gap-2 min-w-0">
                <span className={`w-2 h-2 rounded-full shrink-0 ${resume ? "bg-emerald-500" : "bg-amber-400 animate-pulse"}`} />
                {resume ? (
                  <a
                    href={resume}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-gray-200 hover:text-emerald-400 font-medium truncate flex items-center gap-1.5 hover:underline transition-colors cursor-pointer"
                    title="Open master resume in new tab"
                  >
                    <span className="truncate">Master Resume</span>
                    <svg className="w-3.5 h-3.5 shrink-0 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                ) : (
                  <span className="text-xs text-gray-400 font-medium truncate">
                    No Resume Uploaded
                  </span>
                )}
              </div>

              {/* Upload SVG Action */}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="flex items-center gap-1.5 text-xs text-emerald-400 hover:text-emerald-300 font-semibold px-2.5 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 transition cursor-pointer shrink-0"
                title={resume ? "Upload replacement resume" : "Upload master resume"}
              >
                <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                <span className="text-[11px]">{uploading ? "..." : resume ? "Replace" : "Upload"}</span>
              </button>
            </div>

            {/* 2. Template Selection: Compact Horizontal Strip (MIDDLE) */}
            <div className="flex flex-col gap-1.5 shrink-0">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Template</span>
                <span className="text-[10px] text-emerald-400 font-mono font-semibold">T{selectedTemplate} Active</span>
              </div>
              <div className="flex gap-1.5 overflow-x-auto pb-0.5 snap-x scrollbar-none -mx-0.5 px-0.5">
                {RESUME_TEMPLATES.map((tmpl) => {
                  const isSelected = selectedTemplate === tmpl.id;
                  return (
                    <button
                      key={tmpl.id}
                      type="button"
                      onClick={() => setSelectedTemplate(tmpl.id)}
                      className={`snap-start shrink-0 flex items-center gap-1.5 pl-1.5 pr-2.5 py-1 rounded-lg border cursor-pointer transition-all ${
                        isSelected
                          ? "border-emerald-500 bg-emerald-500/10 ring-1 ring-emerald-500/20"
                          : "border-white/[0.08] bg-white/[0.02] hover:border-white/[0.15]"
                      }`}
                    >
                      <div className="w-7 h-9 rounded overflow-hidden bg-black/50 shrink-0 border border-white/[0.06]">
                        <img src={tmpl.preview} alt={tmpl.name} className="w-full h-full object-cover object-top" />
                      </div>
                      <span className={`text-[11px] font-semibold whitespace-nowrap ${isSelected ? "text-emerald-300" : "text-gray-300"}`}>
                        {tmpl.title.split(" ")[0]}
                      </span>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setInspectingTemplate(tmpl.id);
                        }}
                        className="p-0.5 rounded text-gray-500 hover:text-white transition shrink-0 cursor-pointer"
                        title="Inspect full size"
                      >
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                      </button>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 3. Job Description Input Area (BOTTOM OF COLUMN) */}
            <div className="flex flex-col gap-2 shrink-0">
              <label className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                Job Description
              </label>
              <div className="relative">
                <textarea
                  value={description}
                  onChange={(e) => {
                    setDescription(e.target.value);
                    e.target.style.height = "auto";
                    e.target.style.height = `${Math.min(e.target.scrollHeight, 260)}px`;
                  }}
                  placeholder="Paste job description here..."
                  className="input-dark w-full min-h-[7.5rem] max-h-[17rem] resize-none text-sm leading-relaxed pr-14"
                  rows={4}
                />
                <button
                  type="button"
                  onClick={handleGenerate}
                  disabled={isGenerating || !description.trim()}
                  className={`absolute bottom-3 right-3 w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all shrink-0 z-10 ${
                    isGenerating || !description.trim()
                      ? "bg-emerald-500/30 text-black/40 cursor-not-allowed"
                      : "bg-emerald-500 text-black hover:bg-emerald-400 shadow-lg shadow-emerald-500/25 cursor-pointer"
                  }`}
                >
                  {isGenerating ? (
                    <svg className="animate-spin h-4 w-4 text-black" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 10l7-7m0 0l7 7m-7-7v18" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* ---- RIGHT COLUMN: Desktop Template Showcase Grid ---- */}
          <div className="hidden md:flex w-full md:w-1/2 lg:w-3/5 flex-col surface-card border border-white/[0.08] rounded-2xl p-4 sm:p-6 min-h-[420px] md:h-full overflow-hidden m-3 sm:m-6 ml-0">
            {/* Toolbar: Template Header + Master Resume Status */}
            <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-white/[0.08] shrink-0">
              <div>
                <h3 className="text-gray-200 font-semibold text-sm sm:text-base">
                  Choose Resume Template
                </h3>
                <p className="text-xs text-gray-400">
                  Select your design layout. Preview will synchronize live.
                </p>
              </div>

              {/* Master Resume Status Pill */}
              <div className="flex items-center gap-2 bg-white/[0.04] border border-white/[0.08] px-3 py-1.5 rounded-lg text-xs">
                <span className={`w-2 h-2 rounded-full ${resume ? "bg-emerald-500" : "bg-amber-400 animate-pulse"}`} />
                {resume ? (
                  <a
                    href={resume}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gray-300 hover:text-emerald-400 font-medium truncate max-w-[130px] flex items-center gap-1 hover:underline transition-colors"
                    title="Open master resume"
                  >
                    <span>Master Resume</span>
                    <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                ) : (
                  <span className="text-gray-400 font-medium truncate max-w-[120px]">
                    No Resume Uploaded
                  </span>
                )}
              </div>
            </div>

            {/* Template Gallery Showcase: 2x2 Grid with Full Heights */}
            <div className="flex-1 grid grid-cols-2 gap-4 pt-4 overflow-y-auto min-h-0">
              {RESUME_TEMPLATES.map((tmpl) => {
                const isSelected = selectedTemplate === tmpl.id;
                return (
                  <div
                    key={tmpl.id}
                    onClick={() => setSelectedTemplate(tmpl.id)}
                    className={`group relative rounded-xl border p-2 flex flex-col justify-between transition-all duration-200 cursor-pointer overflow-hidden ${
                      isSelected
                        ? "border-emerald-500 bg-emerald-500/[0.06] shadow-lg shadow-emerald-500/10 ring-1 ring-emerald-500/30"
                        : "border-white/[0.08] bg-white/[0.02] hover:border-white/[0.2] hover:bg-white/[0.04]"
                    }`}
                  >
                    {/* Template Header Badge */}
                    <div className="flex items-center justify-between pb-1.5 px-1">
                      <span className={`text-xs font-semibold ${isSelected ? "text-emerald-300" : "text-gray-200"}`}>
                        {tmpl.title}
                      </span>
                      <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded font-bold ${
                        isSelected
                          ? "bg-emerald-500 text-black"
                          : "bg-white/[0.06] text-gray-400"
                      }`}>
                        T{tmpl.id}
                      </span>
                    </div>

                    {/* Thumbnail Image Container */}
                    <div className="flex-1 bg-black/50 rounded-lg overflow-hidden border border-white/[0.06] relative min-h-[140px] flex items-center justify-center">
                      <img
                        src={tmpl.preview}
                        alt={tmpl.name}
                        className="w-full h-full object-cover object-top transition duration-300 group-hover:scale-[1.02]"
                      />
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setInspectingTemplate(tmpl.id);
                        }}
                        className="absolute bottom-2 right-2 px-2.5 py-1 rounded-lg bg-black/80 hover:bg-emerald-500 text-gray-200 hover:text-black text-xs font-medium border border-white/[0.1] backdrop-blur-sm transition-all shadow flex items-center gap-1 cursor-pointer opacity-90 group-hover:opacity-100"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        <span>Inspect</span>
                      </button>
                    </div>

                    {/* Description Footer */}
                    <p className="text-[11px] text-gray-400 mt-2 line-clamp-1 px-1">
                      {tmpl.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : (
        /* ========================================================= */
        /* PHASE 2: AFTER GENERATION (INTERACTIVE CHATBOT STUDIO)    */
        /* ========================================================= */
        <div className="flex-1 w-full flex flex-col min-h-0 overflow-hidden">
          {/* Rate limit banner */}
          {bannerMessage && (
            <div className="bg-amber-500/10 border-b border-amber-500/30 px-4 py-2 flex items-center justify-between text-xs text-amber-200 shrink-0">
              <div className="flex items-center gap-2">
                <span className="bg-amber-500/20 text-amber-400 font-bold px-1.5 py-0.2 rounded text-[10px] uppercase">Notice</span>
                <span>{bannerMessage}</span>
              </div>
              <button onClick={() => setBannerMessage(null)} className="text-amber-400 hover:text-amber-200 text-sm">✕</button>
            </div>
          )}

          {/* ACTIVE STUDIO: SPLIT CHAT TIMELINE & RESUME STUDIO */}
          <div className="flex-1 w-full h-full flex flex-col md:flex-row min-h-0 overflow-hidden relative">

            {/* MOBILE SEGMENTED CONTROL: [ Live Resume | AI Assistant (N) ] */}
            <div className="md:hidden px-3 py-2 bg-[#121212] border-b border-white/[0.08] flex items-center justify-between shrink-0 z-20">
              <div className="flex items-center bg-black/60 p-1 rounded-xl border border-white/[0.08] w-full">
                <button
                  type="button"
                  onClick={() => setMobileStudioTab("resume")}
                  className={`flex-1 py-1.5 text-xs rounded-lg font-semibold transition flex items-center justify-center gap-1.5 cursor-pointer ${
                    mobileStudioTab === "resume"
                      ? "bg-emerald-500 text-black shadow"
                      : "text-gray-400 hover:text-white"
                  }`}
                >
                  <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>Live Resume</span>
                </button>
                <button
                  type="button"
                  onClick={() => setMobileStudioTab("chat")}
                  className={`flex-1 py-1.5 text-xs rounded-lg font-semibold transition flex items-center justify-center gap-1.5 cursor-pointer relative ${
                    mobileStudioTab === "chat"
                      ? "bg-emerald-500 text-black shadow"
                      : "text-gray-400 hover:text-white"
                  }`}
                >
                  <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  <span>AI Assistant</span>
                  {taggedItems.length > 0 && (
                    <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                      mobileStudioTab === "chat" ? "bg-black text-emerald-400" : "bg-emerald-500 text-black"
                    }`}>
                      {taggedItems.length}
                    </span>
                  )}
                </button>
              </div>
            </div>

            {/* Left Column (Desktop) / Full Chat (Mobile): Chatbot Stream */}
            <div className={`w-full md:w-[42%] lg:w-[38%] flex-1 min-h-0 md:h-full flex-col shrink-0 p-1.5 sm:p-5 overflow-hidden ${
              mobileStudioTab === "chat" ? "flex" : "hidden md:flex"
            }`}>
              <TailorStudioV2Split
                taggedItems={taggedItems}
                onRemoveTag={handleRemoveTag}
                onReviseWithPrompt={handleReviseWithPrompt}
                isRevising={isRevising}
                revisionsRemaining={revisionsRemaining}
                chatMessages={chatMessages}
                onExportPdf={handleExportLatexPdf}
                isExportingPdf={isExportingPdf}
                onStartOver={handleStartOver}
                quickPrompts={QUICK_PROMPTS}
                onToggleTag={handleToggleTag}
                onSwitchToResume={() => setMobileStudioTab("resume")}
              />
            </div>

            {/* Right Column (Desktop) / Full Resume (Mobile): Live Resume Canvas */}
            <div className={`w-full flex-1 min-h-0 md:h-full flex-col surface-card border-0 md:border md:border-white/[0.08] rounded-none md:rounded-2xl overflow-y-auto p-1.5 sm:p-5 bg-black/40 relative ${
              mobileStudioTab === "resume" ? "flex" : "hidden md:flex"
            }`}>
              <div className="flex-1 overflow-y-auto pb-16 md:pb-0">
                {renderResumePreview()}
              </div>

              {/* Floating Bottom Quick Action Bar on Mobile: Jump to Chat when tagging */}
              <div className="md:hidden fixed bottom-3 left-3 right-3 z-30 pointer-events-none">
                <button
                  type="button"
                  onClick={() => setMobileStudioTab("chat")}
                  className="w-full py-2.5 px-4 rounded-xl bg-emerald-500 text-black font-bold text-xs shadow-xl shadow-emerald-500/30 flex items-center justify-between pointer-events-auto hover:bg-emerald-400 transition cursor-pointer border border-emerald-400/50"
                >
                  <div className="flex items-center gap-1.5">
                    <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    <span>Open AI Assistant</span>
                    {taggedItems.length > 0 && (
                      <span className="bg-black text-emerald-300 text-[10px] px-2 py-0.5 rounded-full font-mono">
                        {taggedItems.length} Tagged
                      </span>
                    )}
                  </div>
                  <span>Revise Now →</span>
                </button>
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
};
