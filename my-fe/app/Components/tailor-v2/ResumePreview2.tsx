"use client";

import React from "react";
import { SectionWrapper } from "./SectionWrapper";

interface ResumePreviewProps {
  data: any;
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

function getCleanDomain(url?: string, defaultLabel: string = ""): string {
  if (!url) return defaultLabel;
  try {
    const raw = url.startsWith("http") ? url : `https://${url}`;
    const parsed = new URL(raw);
    let host = parsed.hostname.toLowerCase();
    if (host.startsWith("www.")) host = host.slice(4);
    return host || defaultLabel || url;
  } catch {
    return defaultLabel || url;
  }
}

export const ResumePreview2: React.FC<ResumePreviewProps> = ({
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

  return (
    <div className="w-full flex justify-center py-2 px-2 print:p-0">
      {/* 
        Exact Replica of Template 2 (Resume2.tex.jinja & templete-2.png):
        - ModernCV Classic Blue palette (#1E65A6)
        - Clean two-column table/grid alignment (left metadata | vertical divider | content)
        - Crisp typography with zero emojis
      */}
      <div
        id="resume-a4-canvas"
        className="w-full max-w-[820px] bg-white text-black shadow-2xl p-6 sm:p-10 border border-gray-200 print:border-none print:p-0 print:shadow-none print:w-full print:max-w-none text-[10pt] leading-[1.4] select-text"
        style={{
          fontFamily: "'Latin Modern Roman', 'CMU Serif', 'EB Garamond', 'Times New Roman', serif",
        }}
      >
        {/* HEADER */}
        <SectionWrapper
          sectionKey="header"
          label="Header & Contact"
          isTagged={taggedSectionKeys.has("header")}
          isUpdated={updatedSectionKeys.has("header")}
          onToggleTag={onToggleTag}
        >
          <div className="text-center pb-4 mb-4">
            <h1 className="text-2xl sm:text-3xl font-normal text-black tracking-widest uppercase mb-1">
              {staticProfile.fullname}
            </h1>
            {job?.Role && (
              <h2 className="text-sm sm:text-base font-normal text-[#1E65A6] tracking-wide mb-2">
                {job.Role}
              </h2>
            )}

            <div className="text-[9.5pt] text-gray-700 flex flex-wrap justify-center items-center gap-x-2 gap-y-1">
              {staticProfile.location && <span>{staticProfile.location}</span>}
              {staticProfile.location && staticProfile.phone && <span>|</span>}
              {staticProfile.phone && <span>{staticProfile.phone}</span>}
              {staticProfile.phone && staticProfile.email?.text && <span>|</span>}
              {staticProfile.email?.text && (
                <a
                  href={staticProfile.email.href}
                  className="hover:underline text-[#1E65A6]"
                >
                  {staticProfile.email.text}
                </a>
              )}
            </div>

            <div className="text-[9.5pt] text-gray-700 flex flex-wrap justify-center items-center gap-x-2 gap-y-1 mt-1">
              {staticProfile.linkedin?.href && (
                <a
                  href={staticProfile.linkedin.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline text-[#1E65A6]"
                >
                  LinkedIn
                </a>
              )}
              {staticProfile.github?.href && (
                <>
                  <span>|</span>
                  <a
                    href={staticProfile.github.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:underline text-[#1E65A6]"
                  >
                    GitHub
                  </a>
                </>
              )}
              {staticProfile.portfolio?.href && (
                <>
                  <span>|</span>
                  <a
                    href={staticProfile.portfolio.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:underline text-[#1E65A6]"
                  >
                    Portfolio
                  </a>
                </>
              )}
              {staticProfile.extra_links?.map((el: any, idx: number) => (
                <React.Fragment key={idx}>
                  <span>|</span>
                  <a
                    href={el.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:underline text-[#1E65A6]"
                  >
                    {el.text || "Link"}
                  </a>
                </React.Fragment>
              ))}
            </div>
          </div>
        </SectionWrapper>

        {/* PROFESSIONAL SUMMARY */}
        {job?.professional_summary && (
          <SectionWrapper
            sectionKey="summary"
            label="Professional Summary"
            isTagged={taggedSectionKeys.has("summary")}
            isUpdated={updatedSectionKeys.has("summary")}
            onToggleTag={onToggleTag}
          >
            <div className="mb-5">
              <h3 className="text-sm font-bold uppercase tracking-wider text-[#1E65A6] pb-1 border-b border-[#1E65A6]/40 mb-2">
                PROFESSIONAL SUMMARY
              </h3>
              <p className="text-[9.5pt] text-gray-800 leading-relaxed text-justify">
                {renderTextWithBold(job.professional_summary)}
              </p>
            </div>
          </SectionWrapper>
        )}

        {/* TECHNICAL SKILLS */}
        {job?.skills && job.skills.length > 0 && (
          <SectionWrapper
            sectionKey="skills"
            label="Technical Skills"
            isTagged={taggedSectionKeys.has("skills")}
            isUpdated={updatedSectionKeys.has("skills")}
            onToggleTag={onToggleTag}
          >
            <div className="mb-5">
              <h3 className="text-sm font-bold uppercase tracking-wider text-[#1E65A6] pb-1 border-b border-[#1E65A6]/40 mb-2">
                TECHNICAL SKILLS
              </h3>
              <div className="space-y-1.5 text-[9.5pt]">
                {job.skills.map((skill: any, idx: number) => (
                  <div key={idx} className="flex items-start">
                    <div className="w-[24%] shrink-0 text-right pr-3 font-semibold text-gray-700">
                      {skill.category}
                    </div>
                    <div className="w-[76%] border-l border-gray-300 pl-3.5 text-gray-800">
                      {(skill.values || []).map((v: any, vIdx: number) => (
                        <span key={vIdx}>
                          {v.name}
                          {vIdx < skill.values.length - 1 ? ", " : ""}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </SectionWrapper>
        )}

        {/* EXPERIENCE */}
        {job?.experience && job.experience.length > 0 && (
          <div className="mb-5">
            <h3 className="text-sm font-bold uppercase tracking-wider text-[#1E65A6] pb-1 border-b border-[#1E65A6]/40 mb-2">
              EXPERIENCE
            </h3>
            <div className="space-y-4">
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
                    <div className="flex items-start">
                      <div className="w-[20%] shrink-0 text-right pr-3 text-xs text-gray-500 font-sans pt-0.5">
                        {exp.date}
                      </div>
                      <div className="w-[80%] border-l border-gray-300 pl-3.5">
                        <div className="font-bold text-[10pt] text-black">
                          {exp.Title || exp.title}
                        </div>
                        <div className="text-[9pt] italic text-gray-600 mb-1">
                          {exp.company} {exp.location ? `, ${exp.location}` : ""}
                        </div>
                        <ul className="list-disc pl-4 space-y-1 text-[9pt] text-gray-800 leading-snug">
                          {(exp.points || []).map((pt: string, pIdx: number) => (
                            <li key={pIdx}>{renderTextWithBold(pt)}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </SectionWrapper>
                );
              })}
            </div>
          </div>
        )}

        {/* KEY PROJECTS */}
        {job?.projects && job.projects.length > 0 && (
          <div className="mb-5">
            <SectionWrapper
              sectionKey="projects"
              label="Projects (All / Re-rank)"
              isTagged={taggedSectionKeys.has("projects")}
              isUpdated={updatedSectionKeys.has("projects")}
              onToggleTag={onToggleTag}
            >
              <h3 className="text-sm font-bold uppercase tracking-wider text-[#1E65A6] pb-1 border-b border-[#1E65A6]/40 mb-2">
                KEY PROJECTS
              </h3>
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
                    <div className="flex items-start">
                      <div className="w-[20%] shrink-0 text-right pr-3 text-xs text-gray-500 font-sans pt-0.5">
                        {proj.date || "Ongoing"}
                      </div>
                      <div className="w-[80%] border-l border-gray-300 pl-3.5">
                        <div className="flex justify-between items-baseline mb-0.5">
                          <span className="font-bold text-[10pt] text-black">
                            {proj.name}
                            {proj.project_line && (
                              <span className="font-normal italic text-gray-600 text-[9pt] ml-1.5">
                                — {proj.project_line}
                              </span>
                            )}
                          </span>
                          {proj.href && (
                            <a
                              href={proj.href}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-[8.5pt] text-[#1E65A6] hover:underline"
                            >
                              Link
                            </a>
                          )}
                        </div>
                        <ul className="list-disc pl-4 space-y-1 text-[9pt] text-gray-800 leading-snug">
                          {(proj.points || []).map((pt: string, pIdx: number) => (
                            <li key={pIdx}>{renderTextWithBold(pt)}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </SectionWrapper>
                );
              })}
            </div>
          </div>
        )}

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
              <h3 className="text-sm font-bold uppercase tracking-wider text-[#1E65A6] pb-1 border-b border-[#1E65A6]/40 mb-2">
                EDUCATION
              </h3>
              <div className="space-y-2">
                {staticProfile.education.map((edu: any, idx: number) => (
                  <div key={idx} className="flex items-start">
                    <div className="w-[20%] shrink-0 text-right pr-3 text-xs text-gray-500 font-sans pt-0.5">
                      {edu.date}
                    </div>
                    <div className="w-[80%] border-l border-gray-300 pl-3.5 text-[9.5pt]">
                      <div className="font-bold text-black">{edu.degree}</div>
                      <div className="text-gray-600 text-[9pt]">{edu.institution} {edu.location ? `, ${edu.location}` : ""}</div>
                      {edu.grade && <div className="text-xs text-gray-500">Grade: {edu.grade}</div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </SectionWrapper>
        )}

        {/* CERTIFICATIONS */}
        {staticProfile.certifications && staticProfile.certifications.length > 0 && (
          <SectionWrapper
            sectionKey="certifications"
            label="Certifications"
            isTagged={taggedSectionKeys.has("certifications")}
            isUpdated={updatedSectionKeys.has("certifications")}
            onToggleTag={onToggleTag}
          >
            <div className="mb-5">
              <h3 className="text-sm font-bold uppercase tracking-wider text-[#1E65A6] pb-1 border-b border-[#1E65A6]/40 mb-2">
                CERTIFICATIONS
              </h3>
              <div className="space-y-2 text-[9.5pt]">
                {staticProfile.certifications.map((cert: any, idx: number) => (
                  <div key={idx} className="flex items-start">
                    <div className="w-[20%] shrink-0 text-right pr-3 text-xs text-gray-500 font-sans pt-0.5">•</div>
                    <div className="w-[80%] border-l border-gray-300 pl-3.5">
                      <span className="font-bold text-black">{cert.name}</span>
                      {cert.link && (
                        <a
                          href={cert.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[8.5pt] text-[#1E65A6] hover:underline ml-2"
                        >
                          [Link]
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </SectionWrapper>
        )}

        {/* ACHIEVEMENTS */}
        {job?.achievements && job.achievements.length > 0 && (
          <SectionWrapper
            sectionKey="achievements"
            label="Achievements"
            isTagged={taggedSectionKeys.has("achievements")}
            isUpdated={updatedSectionKeys.has("achievements")}
            onToggleTag={onToggleTag}
          >
            <div className="mb-5">
              <h3 className="text-sm font-bold uppercase tracking-wider text-[#1E65A6] pb-1 border-b border-[#1E65A6]/40 mb-2">
                ACHIEVEMENTS
              </h3>
              <div className="space-y-2 text-[9.5pt]">
                {job.achievements.map((ach: any, idx: number) => (
                  <div key={idx} className="flex items-start">
                    <div className="w-[20%] shrink-0 text-right pr-3 font-semibold text-gray-700">{ach.name}</div>
                    <div className="w-[80%] border-l border-gray-300 pl-3.5 text-gray-800">{ach.description}</div>
                  </div>
                ))}
              </div>
            </div>
          </SectionWrapper>
        )}
      </div>
    </div>
  );
};
