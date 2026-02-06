"use client";
import React, { useEffect, useRef, useState } from "react";
import JobCards from "./JobCards";
import { sendUrl } from "../utiles/agentsCall";
import CryptoJS from "crypto-js";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";
import { API_URL } from "../utiles/api";
import getLoginUser from "../utiles/getUserData";

const steps = [
  { label: "Process started", description: "Fetching relevant Job Titles", min: 0 },
  { label: "Job Titles found!", description: "10%", min: 10 },
  { label: "Getting Jobs from server", description: "40%", min: 20 },
  { label: "Processing Jobs", description: "85%", min: 85 },
  { label: "Select the Jobs to apply!", description: "100%", min: 100 },
];

const Jobs = () => {
  const intervalRef = useRef<number | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [jobs, setJobs] = useState<any>();
  const [url, setUrl] = useState<string>("");
  const [userId, setUserId] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [Progress_userId, setProgress_UserId] = useState<string>("");
  const [linkedin_context, setLinkedin_context] = useState<any>();
  const [callAgent, setCallAgent] = useState<boolean>(false);
  const router = useRouter();

  const ENC_KEY = "qwertyuioplkjhgfdsazxcvbnm987456";
  const IV = "741852963qwerty0";

  function decryptData(ciphertextBase64: string, keyStr: string, ivStr: string) {
    const key = CryptoJS.enc.Utf8.parse(keyStr);
    const iv = CryptoJS.enc.Utf8.parse(ivStr);
    const decrypted = CryptoJS.AES.decrypt(ciphertextBase64, key, {
      iv: iv, mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7,
    });
    return decrypted.toString(CryptoJS.enc.Utf8);
  }

  useEffect(() => {
    async function user() {
      const email = sessionStorage.getItem("email");
      if (email) setProgress_UserId(email);
    }
    user();
  }, []);

  useEffect(() => {
    const pdf = sessionStorage.getItem("resume");
    const context = sessionStorage.getItem("Lcontext");
    if (pdf) setUrl(pdf);
    else {
      toast.error("Resume not found. Please upload your resume");
      router.push("/Jobs/LinkedinUserDetails");
    }
    async function fetchEncryptedCredentials() {
      try {
        const res = await fetch("/api/get-data", { method: "GET", headers: { "Content-Type": "application/json" }, credentials: "include" });
        const json = await res.json();
        if (json.encryptedData) {
          const decrypted = decryptData(json.encryptedData, ENC_KEY, IV);
          const credentials = JSON.parse(decrypted);
          setUserId(credentials.username);
          setPassword(credentials.password);
          setCallAgent(true);
        } else {
          toast.error("Linkedin credentials not provided");
          router.push("/Jobs/LinkedinUserDetails");
        }
      } catch (error: any) {
        toast.error("Error caused by: ", error.message);
      }
    }
    if (context != "true") fetchEncryptedCredentials();
    setLinkedin_context(context);
  }, []);

  useEffect(() => {
    const fetchJobs = async () => {
      if (url === "" || linkedin_context === "") return;
      if (linkedin_context === "true" || callAgent) {
        const { data, error } = await sendUrl(url, userId, password);
        if (data) setJobs(data.jobs);
        else toast.error(`Error from fetching jobs ${error}`);
      }
    };
    fetchJobs();
    if (Progress_userId) {
      intervalRef.current = window.setInterval(() => {
        fetch(`${API_URL}/jobs/${Progress_userId}/progress`)
          .then((res) => res.json())
          .then((data) => {
            let stepIndex = 0;
            for (let i = 0; i < steps.length; i++) {
              if (data.progress == 100) stepIndex = 110;
              else if (data.progress >= steps[i].min) stepIndex = i;
              else break;
            }
            setCurrentStep(stepIndex);
            if (data.progress >= 100 && intervalRef.current) {
              clearInterval(intervalRef.current);
              intervalRef.current = null;
            }
          });
      }, 10000);
      return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
    }
  }, [url, linkedin_context, Progress_userId, callAgent, userId, password]);

  return (
    <div className="flex flex-col lg:flex-row min-h-screen">
      {/* Stepper sidebar */}
      <div className="flex flex-col gap-0 bg-[#111] border-b lg:border-b-0 lg:border-r border-white/[0.06] p-5 md:p-6 lg:p-8 py-8 lg:py-20 w-full lg:w-72 lg:sticky lg:top-[65px] lg:left-0 lg:h-[calc(100vh-65px)] cursor-default">
        <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-6 hidden lg:block">Progress</h3>
        {steps.map((step, index) => (
          <div className="flex items-start" key={step.label}>
            <div className="flex flex-col items-center mr-3 md:mr-4 h-fit">
              <div
                className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all duration-500 ${
                  index < currentStep
                    ? "bg-emerald-500 border-emerald-500"
                    : index === currentStep
                    ? "border-emerald-400 bg-[#0A0A0A] animate-pulse"
                    : "border-white/[0.15] bg-[#0A0A0A]"
                }`}
              >
                {index < currentStep ? (
                  <svg className="w-3 h-3 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : index === currentStep ? (
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                ) : null}
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`w-0.5 h-10 transition-all duration-500 ${
                    index < currentStep ? "bg-emerald-500" : index === currentStep - 1 ? "bg-emerald-500/50" : "bg-white/[0.08]"
                  }`}
                />
              )}
            </div>
            <div className="pb-2">
              <p className={`font-medium text-sm transition-colors ${
                index === currentStep ? "text-emerald-400" : index < currentStep ? "text-white" : "text-gray-600"
              }`}>
                {step.label}
              </p>
              <p className={`text-xs mt-0.5 transition-colors ${
                index === currentStep ? "text-emerald-400/70" : index < currentStep ? "text-gray-400" : "text-gray-700 hidden"
              }`}>
                {step.description}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Job cards area */}
      <div className="flex-1 p-4 md:p-6 lg:p-8">
        {currentStep > 100 ? (
          <JobCards jobs={jobs} />
        ) : (
          <div className="flex items-center justify-center min-h-[60vh] lg:min-h-[80vh]">
            <div className="flex flex-col items-center gap-4">
              <div className="relative">
                <div className="w-12 h-12 rounded-full border-2 border-emerald-500/30 border-t-emerald-500 animate-spin" />
              </div>
              <p className="text-gray-400 text-sm">Finding the best jobs for you...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Jobs;
