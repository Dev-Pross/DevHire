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

export const ResumePreview3: React.FC<ResumePreviewProps> = ({
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
        Exact Replica of Template 3 (Resume3.tex.jinja):
        - Geometric minimalist sans-serif typography
        - Centered LaTeX header with Navy blue (#003C78) role
        - Clean domain links (linkedin.com, github.com, hostnames) separated by bullets (•)
        - Solid black horizontal indicator bar before section headers
        - Full section suite: Summary, Skills, Experience, Projects, Education, Certifications, Achievements
      */}
      <div
        id="resume-a4-canvas"
        className="w-full max-w-[820px] bg-white text-black shadow-2xl p-6 sm:p-10 border border-gray-200 print:border-none print:p-0 print:shadow-none print:w-full print:max-w-none text-[9.5pt] leading-[1.38] select-text font-sans"
      >
        {/* HEADER (Revoked to authentic 2-column split layout with hostnames) */}
        <SectionWrapper
          sectionKey="header"
          label="Header & Contact"
          isTagged={taggedSectionKeys.has("header")}
          isUpdated={updatedSectionKeys.has("header")}
          onToggleTag={onToggleTag}
        >
          <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-8">
            {/* Left: Name and Title */}
            <div>
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-light text-gray-600 uppercase tracking-widest leading-none mb-3">
                {staticProfile.fullname}
              </h1>
              {job?.Role && (
                <h2 className="text-sm sm:text-base font-normal italic text-black">
                  {job.Role}
                </h2>
              )}
            </div>

            {/* Right: Italic Contact Info */}
            <div className="text-right sm:text-right text-xs italic text-gray-700 space-y-0.5 shrink-0 self-end sm:self-start">
              {staticProfile.location && <div>{staticProfile.location}</div>}
              {staticProfile.phone && <div>{staticProfile.phone}</div>}
              {staticProfile.email?.text && (
                <div>
                  <a
                    href={staticProfile.email.href}
                    className="hover:underline text-black font-medium"
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
                    className="hover:underline text-gray-800"
                  >
                    {getCleanDomain(staticProfile.linkedin.href, "linkedin.com")}
                  </a>
                </div>
              )}
              {staticProfile.github?.href && (
                <div>
                  <a
                    href={staticProfile.github.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:underline text-gray-800"
                  >
                    {getCleanDomain(staticProfile.github.href, "github.com")}
                  </a>
                </div>
              )}
              {staticProfile.portfolio?.href && (
                <div>
                  <a
                    href={staticProfile.portfolio.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:underline text-gray-800"
                  >
                    {getCleanDomain(staticProfile.portfolio.href, "portfolio")}
                  </a>
                </div>
              )}
              {staticProfile.extra_links?.map((el: any, eIdx: number) => (
                <div key={eIdx}>
                  <a
                    href={el.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:underline text-gray-800"
                  >
                    {getCleanDomain(el.href, el.text || "link")}
                  </a>
                </div>
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
            <div className="mb-6">
              <div className="flex items-center mb-2.5">
                <span className="w-12 sm:w-16 h-[3.5px] bg-black inline-block mr-3" />
                <h3 className="text-sm sm:text-base font-normal text-black">
                  Professional Summary
                </h3>
              </div>
              <p className="text-[9pt] sm:text-[9.5pt] text-gray-800 leading-relaxed pl-1 sm:pl-3 text-justify">
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
            <div className="mb-6">
              <div className="flex items-center mb-2.5">
                <span className="w-12 sm:w-16 h-[3.5px] bg-black inline-block mr-3" />
                <h3 className="text-sm sm:text-base font-normal text-black">
                  Technical Skills
                </h3>
              </div>
              <div className="space-y-1 pl-1 sm:pl-3 text-[9pt]">
                {job.skills.map((skill: any, idx: number) => (
                  <div key={idx} className="flex">
                    <span className="w-28 sm:w-32 shrink-0 font-medium text-gray-800 text-right pr-3">
                      {skill.category}
                    </span>
                    <span className="text-gray-900">
                      {(skill.values || []).map((v: any, vIdx: number) => (
                        <span key={vIdx}>
                          {v.name}
                          {vIdx < skill.values.length - 1 ? ", " : ""}
                        </span>
                      ))}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </SectionWrapper>
        )}

        {/* EXPERIENCE */}
        {job?.experience && job.experience.length > 0 && (
          <div className="mb-6">
            <div className="flex items-center mb-2.5">
              <span className="w-12 sm:w-16 h-[3.5px] bg-black inline-block mr-3" />
              <h3 className="text-sm sm:text-base font-normal text-black">
                Experience
              </h3>
            </div>
            <div className="space-y-4 pl-1 sm:pl-3">
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
                      <div className="flex justify-between items-baseline mb-0.5">
                        <span className="font-bold text-[9.5pt] text-black">
                          {exp.Title || exp.title} — {exp.company}
                        </span>
                        <span className="text-[8.5pt] text-gray-500 font-normal">
                          {exp.date}
                        </span>
                      </div>
                      <ul className="list-disc pl-4 space-y-0.5 text-[8.5pt] sm:text-[9pt] text-gray-800 leading-snug">
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

        {/* PROJECTS */}
        {job?.projects && job.projects.length > 0 && (
          <div className="mb-6">
            <SectionWrapper
              sectionKey="projects"
              label="Projects (All / Re-rank)"
              isTagged={taggedSectionKeys.has("projects")}
              isUpdated={updatedSectionKeys.has("projects")}
              onToggleTag={onToggleTag}
            >
              <div className="flex items-center mb-2.5">
                <span className="w-12 sm:w-16 h-[3.5px] bg-black inline-block mr-3" />
                <h3 className="text-sm sm:text-base font-normal text-black">
                  Projects
                </h3>
              </div>
            </SectionWrapper>
            <div className="space-y-4 pl-1 sm:pl-3">
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
                        <span className="font-bold text-[9.5pt] text-black">
                          {proj.name}
                          {proj.project_line && (
                            <span className="font-normal italic text-gray-600 text-[8.5pt] ml-1.5">
                              / {proj.project_line}
                            </span>
                          )}
                        </span>
                        {proj.href && (
                          <a
                            href={proj.href}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[8.5pt] text-gray-600 hover:text-black underline"
                          >
                            {getCleanDomain(proj.href, proj.href_name || "demo")}
                          </a>
                        )}
                      </div>
                      <ul className="list-disc pl-4 space-y-0.5 text-[8.5pt] sm:text-[9pt] text-gray-800 leading-snug">
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

        {/* EDUCATION */}
        {staticProfile.education && staticProfile.education.length > 0 && (
          <SectionWrapper
            sectionKey="education"
            label="Education"
            isTagged={taggedSectionKeys.has("education")}
            isUpdated={updatedSectionKeys.has("education")}
            onToggleTag={onToggleTag}
          >
            <div className="mb-6">
              <div className="flex items-center mb-2.5">
                <span className="w-12 sm:w-16 h-[3.5px] bg-black inline-block mr-3" />
                <h3 className="text-sm sm:text-base font-normal text-black">
                  Education
                </h3>
              </div>
              <div className="space-y-2 pl-1 sm:pl-3 text-[9pt]">
                {staticProfile.education.map((edu: any, idx: number) => (
                  <div key={idx} className="flex justify-between items-baseline">
                    <div>
                      <div className="font-medium text-black">{edu.degree}</div>
                      <div className="text-gray-600 text-[8.5pt]">{edu.institution} {edu.location ? `| ${edu.location}` : ""}</div>
                    </div>
                    <div className="text-right text-gray-500 text-xs">
                      {edu.date} {edu.grade ? `| ${edu.grade}` : ""}
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
            <div className="mb-6">
              <div className="flex items-center mb-2.5">
                <span className="w-12 sm:w-16 h-[3.5px] bg-black inline-block mr-3" />
                <h3 className="text-sm sm:text-base font-normal text-black">
                  Certifications
                </h3>
              </div>
              <div className="space-y-1.5 pl-1 sm:pl-3 text-[9pt]">
                {staticProfile.certifications.map((cert: any, idx: number) => (
                  <div key={idx} className="flex justify-between items-baseline">
                    <span className="font-medium text-black">{cert.name}</span>
                    {cert.link && (
                      <a
                        href={cert.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-gray-600 hover:text-black underline ml-2"
                      >
                        [Verify Badge]
                      </a>
                    )}
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
            <div className="mb-6">
              <div className="flex items-center mb-2.5">
                <span className="w-12 sm:w-16 h-[3.5px] bg-black inline-block mr-3" />
                <h3 className="text-sm sm:text-base font-normal text-black">
                  Achievements
                </h3>
              </div>
              <div className="space-y-1.5 pl-1 sm:pl-3 text-[9pt]">
                {job.achievements.map((ach: any, idx: number) => (
                  <div key={idx} className="flex justify-between items-baseline gap-2">
                    <span className="font-medium text-black shrink-0">{ach.name}</span>
                    <span className="text-gray-700 text-xs text-right">{ach.description}</span>
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
