"use client";

import React from "react";
import { SectionWrapper } from "./SectionWrapper";

interface ResumePreviewProps {
  data: any; // Format object
  taggedSectionKeys: Set<string>;
  updatedSectionKeys?: Set<string>;
  onToggleTag: (sectionKey: string, label: string) => void;
}

// Safely parses and renders **bold text** into strong tags
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

export const ResumePreview0: React.FC<ResumePreviewProps> = ({
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
        Exact Replica of Template 0 (Resume0.tex.jinja)
        - 1.5px black outer frame matching templete-0.png
        - Computer Modern Serif LaTeX typography
        - Small-caps section titles with 1px black dividing rule
        - Tight single-page spacing
      */}
      <div
        id="resume-a4-canvas"
        className="w-full max-w-[800px] bg-white text-black shadow-2xl p-6 sm:p-10 print:border-none print:p-0 print:shadow-none print:w-full print:max-w-none text-[10.5pt] leading-[1.35] select-text"
        style={{
          fontFamily: "'KaTeX_Main', 'Latin Modern Roman', 'CMU Serif', 'EB Garamond', 'Times New Roman', serif",
        }}
      >
        {/* ---------- HEADER ---------- */}
        <SectionWrapper
          sectionKey="header"
          label="Header & Contact"
          isTagged={taggedSectionKeys.has("header")}
          isUpdated={updatedSectionKeys.has("header")}
          onToggleTag={onToggleTag}
        >
          <div className="text-center pb-2">
            <h1 className="text-[28px] sm:text-[30px] font-bold text-black tracking-normal leading-tight mb-0.5">
              {staticProfile.fullname}
            </h1>
            {job?.Role && (
              <h2 className="text-[14.5px] sm:text-[15.5px] font-bold text-black tracking-normal mb-1.5">
                {job.Role}
              </h2>
            )}

            {/* Line 1: Location | Phone | Email */}
            <div className="text-[10pt] text-black flex flex-wrap justify-center items-center gap-x-2 gap-y-0.5">
              {staticProfile.location && (
                <span>{staticProfile.location}</span>
              )}
              {staticProfile.location && staticProfile.phone && <span>|</span>}
              {staticProfile.phone && (
                <span>{staticProfile.phone}</span>
              )}
              {staticProfile.phone && staticProfile.email?.text && <span>|</span>}
              {staticProfile.email?.text && (
                <a
                  href={staticProfile.email.href}
                  className="hover:underline text-black"
                >
                  {staticProfile.email.text}
                </a>
              )}
            </div>

            {/* Line 2: LinkedIn | GitHub | Portfolio | extra_links */}
            <div className="text-[10pt] text-black flex flex-wrap justify-center items-center gap-x-2 gap-y-0.5 mt-0.5">
              {staticProfile.linkedin?.href && (
                <a
                  href={staticProfile.linkedin.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline text-black font-medium"
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
                    className="hover:underline text-black font-medium"
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
                    className="hover:underline text-black font-medium"
                  >
                    Portfolio
                  </a>
                </>
              )}
              {staticProfile.extra_links?.map((link: any, idx: number) => (
                <React.Fragment key={idx}>
                  <span>|</span>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:underline text-black font-medium"
                  >
                    {link.text || "Link"}
                  </a>
                </React.Fragment>
              ))}
            </div>
          </div>
        </SectionWrapper>

        {/* ---------- PROFESSIONAL SUMMARY ---------- */}
        {job?.professional_summary && (
          <div className="mt-2.5">
            <h3 className="text-[12pt] font-bold text-black border-b border-black pb-[1px] mb-1.5">
              Professional Summary
            </h3>
            <SectionWrapper
              sectionKey="summary"
              label="Summary"
              isTagged={taggedSectionKeys.has("summary")}
              isUpdated={updatedSectionKeys.has("summary")}
              onToggleTag={onToggleTag}
            >
              <p className="text-[10pt] leading-[1.38] text-black text-justify">
                {renderTextWithBold(job.professional_summary)}
              </p>
            </SectionWrapper>
          </div>
        )}

        {/* ---------- TECHNICAL SKILLS ---------- */}
        {job?.skills && job.skills.length > 0 && (
          <div className="mt-2.5">
            <h3 className="text-[12pt] font-bold text-black border-b border-black pb-[1px] mb-1.5">
              Technical Skills
            </h3>
            <SectionWrapper
              sectionKey="skills"
              label="Skills"
              isTagged={taggedSectionKeys.has("skills")}
              isUpdated={updatedSectionKeys.has("skills")}
              onToggleTag={onToggleTag}
            >
              <div className="space-y-0.5 text-[10pt] leading-[1.38] text-black">
                {job.skills.map((cat: any, idx: number) => (
                  <div key={idx}>
                    <span className="font-bold text-black">{cat.category}: </span>
                    <span>
                      {cat.values?.map((v: any) => v.name || v).join(", ")}
                    </span>
                  </div>
                ))}
              </div>
            </SectionWrapper>
          </div>
        )}

        {/* ---------- PROFESSIONAL EXPERIENCE ---------- */}
        {job?.experience && job.experience.length > 0 && (
          <div className="mt-2.5">
            <h3 className="text-[12pt] font-bold text-black border-b border-black pb-[1px] mb-1.5">
              Professional Experience
            </h3>
            <div className="space-y-2">
              {job.experience.map((exp: any, idx: number) => {
                const sKey = `experience.${idx}`;
                return (
                  <div key={idx} className="break-inside-avoid">
                    <SectionWrapper
                      sectionKey={sKey}
                      label={`Experience · ${exp.company || exp.Title}`}
                      isTagged={taggedSectionKeys.has(sKey)}
                      isUpdated={updatedSectionKeys.has(sKey)}
                      onToggleTag={onToggleTag}
                    >
                      {/* Line 1: Title (Bold Left) | Location (Right) */}
                      <div className="flex justify-between items-baseline text-[10.5pt] text-black">
                        <span className="font-bold">
                          {exp.Title || exp.title}
                        </span>
                        <span className="text-[10pt] text-right">
                          {exp.location}
                        </span>
                      </div>

                      {/* Line 2: Company (Italic Left) | Date (Italic Right) */}
                      <div className="flex justify-between items-baseline text-[10pt] italic text-black mb-0.5">
                        <span>{exp.company}</span>
                        <span className="text-right">{exp.date}</span>
                      </div>

                      {/* Bullet points */}
                      <ul className="list-disc pl-5 text-[10pt] leading-[1.35] text-black space-y-0.5">
                        {exp.points?.map((pt: string, pIdx: number) => (
                          <li key={pIdx}>{renderTextWithBold(pt)}</li>
                        ))}
                      </ul>
                    </SectionWrapper>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ---------- KEY PROJECTS ---------- */}
        {job?.projects && job.projects.length > 0 && (
          <div className="mt-2.5">
            <SectionWrapper
              sectionKey="projects"
              label="Projects (All / Re-rank)"
              isTagged={taggedSectionKeys.has("projects")}
              isUpdated={updatedSectionKeys.has("projects")}
              onToggleTag={onToggleTag}
            >
              <h3 className="text-[12pt] font-bold text-black border-b border-black pb-[1px] mb-1.5">
                Key Projects
              </h3>
            </SectionWrapper>
            <div className="space-y-2">
              {job.projects.map((proj: any, idx: number) => {
                const sKey = `projects.${idx}`;
                return (
                  <div key={idx} className="break-inside-avoid">
                    <SectionWrapper
                      sectionKey={sKey}
                      label={`Project · ${proj.name}`}
                      isTagged={taggedSectionKeys.has(sKey)}
                      isUpdated={updatedSectionKeys.has(sKey)}
                      onToggleTag={onToggleTag}
                    >
                      {/* Line 1: Project Name (Bold Left); Link on Right */}
                      <div className="flex justify-between items-baseline text-[10.5pt] text-black">
                        <div>
                          <span className="font-bold">{proj.name}</span>
                        </div>
                        {proj.href && (
                          <a
                            href={proj.href}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[10pt] text-black hover:underline"
                          >
                            {proj.href_name || "Link"}
                          </a>
                        )}
                      </div>

                      {/* Bullet points */}
                      <ul className="list-disc pl-5 text-[10pt] leading-[1.35] text-black space-y-0.5 mt-0.5">
                        {proj.points?.map((pt: string, pIdx: number) => (
                          <li key={pIdx}>{renderTextWithBold(pt)}</li>
                        ))}
                      </ul>
                    </SectionWrapper>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ---------- ACHIEVEMENTS ---------- */}
        {job?.achievements && job.achievements.length > 0 && (
          <div className="mt-2.5 break-inside-avoid">
            <h3 className="text-[12pt] font-bold text-black border-b border-black pb-[1px] mb-1.5">
              Achievements
            </h3>
            <SectionWrapper
              sectionKey="achievements"
              label="Achievements"
              isTagged={taggedSectionKeys.has("achievements")}
              isUpdated={updatedSectionKeys.has("achievements")}
              onToggleTag={onToggleTag}
            >
              <div className="space-y-1 text-[10pt] leading-[1.35] text-black">
                {job.achievements.map((ach: any, idx: number) => (
                  <div key={idx}>
                    <span className="font-bold">{ach.name}: </span>
                    <span>{ach.description}</span>
                  </div>
                ))}
              </div>
            </SectionWrapper>
          </div>
        )}

        {/* ---------- EDUCATION ---------- */}
        {staticProfile.education && staticProfile.education.length > 0 && (
          <div className="mt-2.5 break-inside-avoid">
            <h3 className="text-[12pt] font-bold text-black border-b border-black pb-[1px] mb-1.5">
              Education
            </h3>
            <SectionWrapper
              sectionKey="education"
              label="Education"
              isTagged={taggedSectionKeys.has("education")}
              isUpdated={updatedSectionKeys.has("education")}
              onToggleTag={onToggleTag}
            >
              <div className="space-y-1.5">
                {staticProfile.education.map((edu: any, idx: number) => (
                  <div key={idx}>
                    {/* Line 1: Institution (Bold Left) | Location (Right) */}
                    <div className="flex justify-between items-baseline text-[10.5pt] text-black">
                      <span className="font-bold">{edu.institution}</span>
                      <span className="text-[10pt] text-right">{edu.location}</span>
                    </div>
                    {/* Line 2: Degree (Italic Left) | Date (Italic Right) */}
                    <div className="flex justify-between items-baseline text-[10pt] italic text-black">
                      <span>{edu.degree}</span>
                      <span className="text-right">{edu.date}</span>
                    </div>
                  </div>
                ))}
              </div>
            </SectionWrapper>
          </div>
        )}

        {/* ---------- CERTIFICATIONS ---------- */}
        {staticProfile.certifications && staticProfile.certifications.length > 0 && (
          <div className="mt-2.5 break-inside-avoid">
            <h3 className="text-[12pt] font-bold text-black border-b border-black pb-[1px] mb-1.5">
              Certifications
            </h3>
            <SectionWrapper
              sectionKey="certifications"
              label="Certifications"
              isTagged={taggedSectionKeys.has("certifications")}
              isUpdated={updatedSectionKeys.has("certifications")}
              onToggleTag={onToggleTag}
            >
              <div className="space-y-1 text-[10pt] leading-[1.35] text-black">
                {staticProfile.certifications.map((cert: any, idx: number) => (
                  <div key={idx}>
                    <span className="font-bold">{cert.name}</span>
                    {cert.link && (
                      <span className="ml-1.5">
                        –{" "}
                        <a
                          href={cert.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:underline text-[9.5pt]"
                        >
                          [Verify Badge]
                        </a>
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </SectionWrapper>
          </div>
        )}
      </div>
    </div>
  );
};
