"use client";
import React, { useEffect, useRef, useState } from "react";
import { Apply_Jobs } from "../utiles/agentsCall";
import CryptoJS from "crypto-js";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { API_URL } from "../utiles/api";
import getLoginUser from "../utiles/getUserData";

interface jobsData {
  job_url: string;
  job_description: string;
}

interface ApplyProps {
  url?: string;
  userId?: string;
  password?: string;
  jobs?: jobsData[];
}

const Apply: React.FC<ApplyProps> = () => {
  const steps = [
    { label: "Processing jobs", description: "1%", min: 0 },
    { label: "Tailoring Resume", description: "10%", min: 10 },
    { label: "Processing Resumes", description: "40%", min: 20 },
    { label: "Applying Jobs", description: "85%", min: 85 },
    { label: "Applied Successfully", description: "100%", min: 100 },
  ];
  const intervalRef = useRef<number | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [response, setResponse] = useState<any>(null);
  const [Progress_userId, setProgress_UserId] = useState<string>("");
  const [jobs, setJobs] = useState<{ job_url: string; job_description: string }[]>([]);
  const router = useRouter();
  const [url, setUrl] = useState<string>("");
  const [userId, setUserId] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [user, setUser] = useState<string | null>(null);
  const [dbData, setDbData] = useState<any>();

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
    const pdf = sessionStorage.getItem("resume");
    const context = sessionStorage.getItem("Lcontext");
    if (pdf) setUrl(pdf);
    else {
      toast.error("Resume not found. Please upload your resume");
      router.push("/Jobs/LinkedinUserDetails");
    }
    const job_data = sessionStorage.getItem("jobs");
    const id = sessionStorage.getItem("id");
    if (job_data != null) setJobs(JSON.parse(job_data));
    else {
      toast.error("No jobs found to proceed");
      router.push("/Jobs");
    }
    if (id != null) setUser(id);
    else toast.error("Please Login to start");

    async function fetchEncryptedCredentials() {
      try {
        const res = await fetch("/api/get-data", { method: "GET", headers: { "Content-Type": "application/json" }, credentials: "include" });
        const json = await res.json();
        if (json.encryptedData) {
          const decrypted = decryptData(json.encryptedData, ENC_KEY, IV);
          const credentials = JSON.parse(decrypted);
          setUserId(credentials.username);
          setPassword(credentials.password);
        } else {
          toast.error("Linkedin credentials not provided");
          router.push("/Jobs/LinkedinUserDetails");
        }
      } catch (error: any) {
        toast.error("Error caused by: ", error.message);
      }
    }
    if (context != "true") fetchEncryptedCredentials();

    async function getAppliedJobs() {
      const res = await fetch(`/api/User?id=${user}`, { method: "GET", headers: { "Content-Type": "application/json" }, credentials: "include" });
      const my_data = await res.json();
      if (res) setDbData(my_data.user.applied_jobs);
    }
    if (user) getAppliedJobs();
  }, [user, router]);

  useEffect(() => {
    async function user() {
      const { data, error } = await getLoginUser();
      if (data?.user) setProgress_UserId(data.user.user_metadata.email);
    }
    user();
  }, []);

  useEffect(() => {
    if (!jobs || jobs.length === 0) return;
    if (!user) return;
    if (!dbData) return;
    if (!Progress_userId) return;

    async function apply() {
      try {
        const { data, error } = await Apply_Jobs(jobs, url, userId, password);
        if (data) {
          sessionStorage.setItem("applied", data.successful_applications.flat(Infinity).length);
          const payload = [...new Set([...dbData, ...data.successful_applications.flat(Infinity)])];
          const res = await fetch("/api/User?action=update", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: user, data: { column: "applied_jobs", value: payload } }),
          });
          if (res.ok) console.log("data pushed");
          else console.log("data pushed failed");
          setResponse(data);
        } else {
          toast.error("Error from fetching jobs: ", error?.status);
          if (error.status === 500) toast.error("Can't reach server, please try again");
        }
      } catch (error: any) {
        toast.error("Error in applying jobs ", error.message);
      }
    }

    apply();

    if (Progress_userId) {
      intervalRef.current = window.setInterval(() => {
        fetch(`${API_URL}/apply/${Progress_userId}/progress`)
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
      }, 2000);
      return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
    } else {
      toast.error("Linkedin credentials not provided");
      router.push("/Jobs/LinkedinUserDetails");
    }
  }, [user, jobs, dbData, Progress_userId]);

  return (
    <div className="w-full min-h-screen overflow-x-hidden flex flex-col">
      {/* Mobile vertical stepper */}
      <div className="lg:hidden shrink-0 flex flex-col gap-0 bg-[#111] border-b border-white/[0.06] p-5 py-8 w-full cursor-default">
        {steps.map((step, index) => (
          <div className="flex items-start" key={step.label}>
            <div className="flex flex-col items-center mr-3 h-fit">
              <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all duration-500 ${
                index < currentStep ? "bg-emerald-500 border-emerald-500"
                  : index === currentStep ? "border-emerald-400 bg-[#0A0A0A] animate-pulse"
                  : "border-white/[0.15] bg-[#0A0A0A]"
              }`}>
                {index < currentStep ? (
                  <svg className="w-3 h-3 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : index === currentStep ? (
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                ) : null}
              </div>
              {index < steps.length - 1 && (
                <div className={`w-0.5 h-10 transition-all duration-500 ${
                  index < currentStep ? "bg-emerald-500" : "bg-white/[0.08]"
                }`} />
              )}
            </div>
            <div className="pb-2">
              <p className={`font-medium text-sm ${
                index === currentStep ? "text-emerald-400" : index < currentStep ? "text-white" : "text-gray-600"
              }`}>{step.label}</p>
              <p className={`text-xs mt-0.5 ${
                index === currentStep ? "text-emerald-400/70" : index < currentStep ? "text-gray-400" : "text-gray-700 hidden"
              }`}>{step.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Desktop horizontal stepper */}
      <div className="hidden lg:flex shrink-0 justify-center gap-0 p-12 py-16 w-full sticky top-[65px] bg-[#0A0A0A]/80 backdrop-blur-xl z-10 border-b border-white/[0.06] cursor-default">
        {steps.map((step, index) => (
          <div className="flex flex-col items-start" key={step.label}>
            <div className="flex items-center mr-1 h-fit">
              <div className={`w-12 h-12 rounded-full border-2 flex items-center justify-center transition-all duration-500 ${
                index < currentStep ? "bg-emerald-500 border-emerald-500"
                  : index === currentStep ? "border-emerald-400 bg-[#0A0A0A]"
                  : "border-white/[0.15] bg-[#0A0A0A]"
              }`}>
                {index < currentStep ? (
                  <svg className="w-5 h-5 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : index === currentStep ? (
                  <div className="w-4 h-4 rounded-full border-2 border-emerald-400 border-t-transparent animate-spin" />
                ) : null}
              </div>
              {index < steps.length - 1 && (
                <div className={`lg:w-28 xl:w-40 h-0.5 transition-all duration-500 ${
                  index < currentStep ? "bg-emerald-500" : "bg-white/[0.08]"
                }`} />
              )}
            </div>
            <p className={`font-medium text-sm pt-3 ${
              index === currentStep ? "text-emerald-400" : index < currentStep ? "text-white" : "text-gray-600"
            }`}>{step.label}</p>
            <p className={`text-xs mt-0.5 ${
              index === currentStep ? "text-emerald-400/70" : index < currentStep ? "text-gray-400" : "text-gray-700 hidden"
            }`}>{step.description}</p>
          </div>
        ))}
      </div>

      {/* Results */}
      {response && currentStep > 100 && (
        <div className="p-8 lg:p-16">
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            {[
              { label: "Total Jobs", value: response.total_jobs, color: "text-white" },
              { label: "Successful", value: response.successful_applications.flat(Infinity).length, color: "text-emerald-400" },
              { label: "Failed", value: response.failed_applications.flat(Infinity).length, color: "text-red-400" },
            ].map((stat) => (
              <div key={stat.label} className="surface-card p-6 text-center">
                <p className="text-sm text-gray-400 mb-1">{stat.label}</p>
                <p className={`text-3xl font-bold ${stat.color}`}>{stat.value}</p>
              </div>
            ))}
          </div>
          <a
            href="https://www.linkedin.com/my-items/saved-jobs/?cardType=APPLIED"
            target="_blank"
            className="block text-center"
          >
            <div className="surface-card p-6 hover:border-emerald-500/30 transition-all">
              <p className="text-emerald-400 text-lg font-semibold">Track your applications on LinkedIn →</p>
            </div>
          </a>
        </div>
      )}
    </div>
  );
};

export default Apply;
