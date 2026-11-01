"use client";

import React from "react";
import { SectionWrapper } from "./SectionWrapper";

interface ResumePreviewProps {
  data: any; // Format object
  taggedSectionKeys: Set<string>;
  updatedSectionKeys?: Set<string>;
  onToggleTag: (sectionKey: string, label: string) => void;
}

function renderTextWithBold(raw: string) {
  if (!raw) return null;
  const parts = raw.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={index} className="font-bold text-black">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <span key={index}>{part}</span>;
  });
}

export const ResumePreview1: React.FC<ResumePreviewProps> = ({
  data,
  taggedSectionKeys,
  updatedSectionKeys = new Set(),
  onToggleTag,
}) => {
  if (!data || !data.static_profile) {
    return (
      <div className="flex items-center justify-center p-12 text-gray-400">
        No resume data available.
      </div>
    );
  }

  const staticProfile = data.static_profile;
  const job = data.tailored_jobs && data.tailored_jobs.length > 0 ? data.tailored_jobs[0] : null;

  // Flatten skills with score/level fallback for progress meters
  const skillList: Array<{ name: string; level: string; score: number }> = [];
  if (job?.skills) {
    job.skills.forEach((cat: any) => {
      (cat.values || []).forEach((v: any) => {
        if (skillList.length < 12) {
          skillList.push({
            name: v.name,
            level: v.level || (v.score && v.score > 0.8 ? "Advanced" : "Proficient"),
            score: typeof v.score === "number" ? Math.min(Math.max(v.score, 0.4), 1.0) : 0.85,
          });
        }
      });
    });
  }

  return (
    <div className="w-full flex justify-center py-2 px-2 print:p-0">
      {/* 
        Exact Replica of Template 1 (Resume1.tex.jinja & templete-1.png):
        - Palatino serif typography
        - Dark charcoal banner for candidate identity
        - Two-column layout (30% left / 70% right)
        - Crimson (#B90000) skill progress meters and date badges
      */}
      <div
        id="resume-a4-canvas"
        className="w-full max-w-[820px] bg-white text-[#222] shadow-2xl p-6 sm:p-8 border border-gray-300 print:border-none print:p-0 print:shadow-none print:w-full print:max-w-none text-[10pt] leading-[1.38] select-text"
        style={{
          fontFamily: "'Palatino Linotype', 'Book Antiqua', Palatino, 'Georgia', serif",
        }}
      >
        {/* Top Charcoal Header Banner */}
        <SectionWrapper
          sectionKey="header"
          label="Header & Identity"
          isTagged={taggedSectionKeys.has("header")}
          isUpdated={updatedSectionKeys.has("header")}
          onToggleTag={onToggleTag}
        >
          <div className="bg-[#3D4043] text-white p-5 text-center mb-6 shadow-sm">
            <h1 className="text-2xl sm:text-3xl font-normal uppercase tracking-[0.2em] text-white">
              {staticProfile.fullname}
            </h1>
            <div className="w-16 h-[1.5px] bg-white/40 mx-auto my-2" />
            <h2 className="text-xs sm:text-sm font-normal text-gray-200 tracking-wide">
              {job?.Role || "Software Professional"}
            </h2>
          </div>
        </SectionWrapper>

        {/* 2-Column Split */}
        <div className="flex flex-col sm:flex-row gap-6">
          {/* ================= LEFT COLUMN (30%) ================= */}
          <div className="w-full sm:w-[32%] shrink-0 flex flex-col gap-6">
            {/* SKILLS WITH PROGRESS BARS */}
            <SectionWrapper
              sectionKey="skills"
              label="Technical Skills"
              isTagged={taggedSectionKeys.has("skills")}
              isUpdated={updatedSectionKeys.has("skills")}
              onToggleTag={onToggleTag}
            >
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#3D4043] mb-1">
                  SKILLS
                </h3>
                <div className="w-12 h-[2.5px] bg-[#B90000] mb-3.5" />

                <div className="space-y-3">
                  {skillList.map((s, idx) => (
                    <div key={idx} className="text-[9pt]">
                      <div className="flex justify-between items-baseline mb-0.5">
                        <span className="font-bold text-[#111]">{s.name}</span>
                        <span className="text-[8pt] text-gray-500 font-sans">{s.level}</span>
                      </div>
                      <div className="w-full bg-gray-200 h-[3px]">
                        <div
                          className="bg-[#B90000] h-full"
                          style={{ width: `${Math.round(s.score * 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </SectionWrapper>

            {/* CONTACT INFO */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#3D4043] mb-1">
                CONTACT
              </h3>
              <div className="w-12 h-[2.5px] bg-[#B90000] mb-3" />

              <div className="space-y-1.5 text-[9pt] text-[#444]">
                {staticProfile.location && (
                  <div>{staticProfile.location}</div>
                )}
                {staticProfile.phone && (
                  <div>{staticProfile.phone}</div>
                )}
                {staticProfile.email?.text && (
                  <div>
                    <a
                      href={staticProfile.email.href}
                      className="hover:underline text-[#B90000] break-all"
                    >
                      {staticProfile.email.text}
                    </a>
                  </div>
                )}
                {staticProfile.linkedin?.href && (
                  <div>
                    <a
                      href={staticProfile.linkedin.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:underline text-[#B90000]"
                    >
                      LinkedIn
                    </a>
                  </div>
                )}
                {staticProfile.github?.href && (
                  <div>
                    <a
                      href={staticProfile.github.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:underline text-[#B90000]"
                    >
                      GitHub
                    </a>
                  </div>
                )}
                {staticProfile.portfolio?.href && (
                  <div>
                    <a
                      href={staticProfile.portfolio.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:underline text-[#B90000]"
                    >
                      Portfolio
                    </a>
                  </div>
                )}
              </div>
            </div>

            {/* EDUCATION */}
            {staticProfile.education && staticProfile.education.length > 0 && (
              <SectionWrapper
                sectionKey="education"
                label="Education"
                isTagged={taggedSectionKeys.has("education")}
                isUpdated={updatedSectionKeys.has("education")}
                onToggleTag={onToggleTag}
              >
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#3D4043] mb-1">
                    EDUCATION
                  </h3>
                  <div className="w-12 h-[2.5px] bg-[#B90000] mb-3" />

                  <div className="space-y-3 text-[9pt]">
                    {staticProfile.education.map((edu: any, idx: number) => (
                      <div key={idx}>
                        <div className="font-bold text-[#111]">{edu.degree}</div>
                        <div className="text-gray-600 text-[8.5pt]">{edu.institution}</div>
                        <div className="text-gray-500 text-[8pt] font-sans">
                          {edu.date} {edu.grade ? `| ${edu.grade}` : ""}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </SectionWrapper>
            )}
          </div>

          {/* ================= RIGHT COLUMN (70%) ================= */}
          <div className="w-full sm:w-[68%] flex flex-col gap-6">
            {/* PROFILE / PROFESSIONAL SUMMARY */}
            {job?.professional_summary && (
              <SectionWrapper
                sectionKey="summary"
                label="Professional Summary"
                isTagged={taggedSectionKeys.has("summary")}
                isUpdated={updatedSectionKeys.has("summary")}
                onToggleTag={onToggleTag}
              >
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#3D4043] mb-1">
                    PROFILE
                  </h3>
                  <div className="w-12 h-[2.5px] bg-[#B90000] mb-2.5" />
                  <p className="text-[9.5pt] text-[#333] leading-relaxed text-justify">
                    {renderTextWithBold(job.professional_summary)}
                  </p>
                </div>
              </SectionWrapper>
            )}

            {/* WORK EXPERIENCE */}
            {job?.experience && job.experience.length > 0 && (
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#3D4043] mb-1">
                  WORK EXPERIENCE
                </h3>
                <div className="w-12 h-[2.5px] bg-[#B90000] mb-3" />

                <div className="space-y-5">
                  {job.experience.map((exp: any, idx: number) => {
                    const secKey = `experience.${idx}`;
                    return (
                      <SectionWrapper
                        key={idx}
                        sectionKey={secKey}
                        label={`${exp.Title || exp.title} @ ${exp.company}`}
                        isTagged={taggedSectionKeys.has(secKey)}
                        isUpdated={updatedSectionKeys.has(secKey)}
                        onToggleTag={onToggleTag}
                      >
                        <div>
                          <div className="flex justify-between items-start gap-2 mb-1">
                            <div>
                              <div className="font-bold text-[10.5pt] text-[#111]">
                                {exp.Title || exp.title}
                              </div>
                              <div className="text-[9pt] italic text-gray-700">
                                {exp.company} {exp.location ? `- ${exp.location}` : ""}
                              </div>
                            </div>
                            {exp.date && (
                              <div className="bg-[#B90000] text-white px-2 py-0.5 text-[8pt] font-bold uppercase tracking-wider shrink-0 font-sans">
                                {exp.date}
                              </div>
                            )}
                          </div>

                          <ul className="list-disc pl-4 space-y-1 text-[9.5pt] text-[#333] leading-snug">
                            {(exp.points || []).map((pt: string, pIdx: number) => (
                              <li key={pIdx}>{renderTextWithBold(pt)}</li>
                            ))}
                          </ul>
                        </div>
                      </SectionWrapper>
                    );
                  })}
                </div>
              </div>
            )}

            {/* KEY PROJECTS */}
            {job?.projects && job.projects.length > 0 && (
              <div>
                <SectionWrapper
                  sectionKey="projects"
                  label="Projects (All / Re-rank)"
                  isTagged={taggedSectionKeys.has("projects")}
                  isUpdated={updatedSectionKeys.has("projects")}
                  onToggleTag={onToggleTag}
                >
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#3D4043] mb-1">
                    KEY PROJECTS
                  </h3>
                  <div className="w-12 h-[2.5px] bg-[#B90000] mb-3" />
                </SectionWrapper>

                <div className="space-y-4">
                  {job.projects.map((proj: any, idx: number) => {
                    const secKey = `projects.${idx}`;
                    return (
                      <SectionWrapper
                        key={idx}
                        sectionKey={secKey}
                        label={proj.name}
                        isTagged={taggedSectionKeys.has(secKey)}
                        isUpdated={updatedSectionKeys.has(secKey)}
                        onToggleTag={onToggleTag}
                      >
                        <div>
                          <div className="flex justify-between items-baseline mb-0.5">
                            <span className="font-bold text-[10pt] text-[#111]">
                              {proj.name}
                              {proj.project_line && (
                                <span className="font-normal italic text-gray-600 text-[9pt] ml-1.5">
                                  | {proj.project_line}
                                </span>
                              )}
                            </span>
                            {proj.href && (
                              <a
                                href={proj.href}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-[8.5pt] text-[#B90000] hover:underline font-medium"
                              >
                                {proj.href_name || "Link"}
                              </a>
                            )}
                          </div>

                          <ul className="list-disc pl-4 space-y-1 text-[9.5pt] text-[#333] leading-snug">
                            {(proj.points || []).map((pt: string, pIdx: number) => (
                              <li key={pIdx}>{renderTextWithBold(pt)}</li>
                            ))}
                          </ul>
                        </div>
                      </SectionWrapper>
                    );
                  })}
                </div>
              </div>
            )}

            {/* CERTIFICATIONS */}
            {staticProfile.certifications && staticProfile.certifications.length > 0 && (
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#3D4043] mb-1">
                  CERTIFICATIONS
                </h3>
                <div className="w-12 h-[2.5px] bg-[#B90000] mb-3" />

                <div className="space-y-2">
                  {staticProfile.certifications.map((cert: any, idx: number) => {
                    const secKey = `certifications.${idx}`;
                    return (
                      <SectionWrapper
                        key={idx}
                        sectionKey={secKey}
                        label={cert.name}
                        isTagged={taggedSectionKeys.has(secKey)}
                        isUpdated={updatedSectionKeys.has(secKey)}
                        onToggleTag={onToggleTag}
                      >
                        <div className="flex justify-between items-baseline text-[9.5pt]">
                          <span className="font-bold text-[#111]">{cert.name}</span>
                          {cert.link && (
                            <a
                              href={cert.link}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-[8.5pt] text-[#B90000] hover:underline font-medium"
                            >
                              [Verify Badge]
                            </a>
                          )}
                        </div>
                      </SectionWrapper>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
