"use client";
import React, { useEffect, useRef, useState } from "react";
import { Apply_Jobs } from "../utiles/agentsCall";
import CryptoJS from "crypto-js";
import { PrismaClient } from "@prisma/client";
const primsa = new PrismaClient();
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
    {
      label: "Processing jobs",
      description: "1%",
      min: 0,
    },
    {
      label: "Talioring Resume",
      description: "10%",
      min: 10,
    },
    {
      label: "Proccessing Resumes",
      description: "40%",
      min: 20,
    },
    {
      label: "Applying Jobs",
      description: "85%",
      min: 85,
    },
    {
      label: "Applied Successfully",
      description: "100%",
      min: 100,
    },
  ];
  const intervalRef = useRef<number | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [response, setResponse] = useState<any>(null);
  const [jobs, setJobs] = useState<
    { job_url: string; job_description: string }[]
  >([]);

  const [url, setUrl] = useState<string>("");
  const [userId, setUserId] = useState<string>("");
  const [password, setPassword] = useState<string>("");

  const ENC_KEY = "qwertyuioplkjhgfdsazxcvbnm987456"; // ensure 32 bytes for AES-256
  const IV = "741852963qwerty0";

  function decryptData(
    ciphertextBase64: string,
    keyStr: string,
    ivStr: string
  ) {
    const key = CryptoJS.enc.Utf8.parse(keyStr);
    const iv = CryptoJS.enc.Utf8.parse(ivStr);

    const decrypted = CryptoJS.AES.decrypt(ciphertextBase64, key, {
      iv: iv,
      mode: CryptoJS.mode.CBC,
      padding: CryptoJS.pad.Pkcs7,
    });
    return decrypted.toString(CryptoJS.enc.Utf8);
  }

  useEffect(() => {
    const pdf = sessionStorage.getItem("resume");
    if (pdf) setUrl(pdf);

    async function fetchEncryptedCredentials() {
      try {
        const res = await fetch("http://localhost:3000/api/get-data", {
          method: "GET",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        });

        const json = await res.json();

        if (json.encryptedData) {
          const decrypted = decryptData(json.encryptedData, ENC_KEY, IV);
          const credentials = JSON.parse(decrypted);
          setUserId(credentials.username);
          setPassword(credentials.password);
          console.log("Decrypted user credentials:", userId, " ", password);
        } else {
          console.error("No encryptedData in response");
        }
      } catch (error) {
        console.error("Error fetching or decrypting credentials:", error);
      }
    }

    fetchEncryptedCredentials();
  }, []);

  useEffect(() => {
    const job_data = sessionStorage.getItem("jobs");
    if (job_data) {
      setJobs(JSON.parse(job_data));
    }
    console.log("jobs from ls: ", job_data);
  }, []);

  console.log("jobs state", jobs);

  useEffect(() => {
    if (!jobs || jobs.length === 0) return;
    async function apply() {
      const { data, error } = await Apply_Jobs(jobs, url, userId, password);
      try {
        if (data) {
          await primsa.user.create({
            data: {
              email: "",
              name: userId,
              applied_jobs: data.successful_applications[0].length,
              // applied_jobs: data.successful_applications[0],

              // failed_jobs: data.failed_applications[0].length,
              // total_jobs: data.total_jobs,
            },
          });
          setResponse(data);
        } else console.log("error from fetching jobs ", error);
      } catch (error) {
        console.log("error in applying jobs ", error);
      }
    }
    apply();

    if (userId) {
      console.log("all set to start apply");

      intervalRef.current = window.setInterval(() => {
        fetch(`http://127.0.0.1:8000/apply/${userId}/progress`)
          .then((res) => res.json())
          .then((data) => {
            console.log("progress: ", data.progress);
            // setPercentage(data.progress)
            let stepIndex = 0;
            for (let i = 0; i < steps.length; i++) {
              if (data.progress == 100) {
                stepIndex = 110;
              } else if (data.progress >= steps[i].min) {
                stepIndex = i;
              } else {
                break;
              }
            }
            setCurrentStep(stepIndex);
            if (data.progress >= 100 && intervalRef.current) {
              clearInterval(intervalRef.current);
              intervalRef.current = null;
            }
          });
      }, 2000);
      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    } else {
      console.log("user id not provided");
    }
  }, [userId]);

  console.log("apply server output ", response);

  return (
    <>
      <div className="h-screen">
        <div className="flex justify-center gap-0 bg-transparent p-18 py-20 shadow-lg shadow-[#052718]-500 w-full max-w-screen sticky top-15 mt-10  rounded-r-lg cursor-default">
          {steps.map((step, index) => (
            <div className="flex flex-col item-start" key={step.label}>
              <div className="flex  items-center mr-1 h-fit">
                <div
                  className={`
                                    w-15 h-15 rounded-full border-2 flex items-center justify-center transition-all duration-900 
                                    ${
                                      index < currentStep
                                        ? "bg-blue-600 border-blue-600"
                                        : index === currentStep
                                        ? "border-blue-500  shadow-white-500 bg-white "
                                        : "border-gray-600 bg-[#13182c] animate-pulse"
                                    }
                                    `}
                >
                  {index < currentStep ? (
                    <svg width="30" height="30">
                      <circle cx="15" cy="15" r="14" fill="#fff" />
                    </svg>
                  ) : index === currentStep ? (
                    // <div className="w-3 h-10 rounded-full bg-blue-400 animate-spin" />
                    <div
                      className={`bg-[url('/spinner.svg')] w-15 h-15 bg-no-repeat`}
                    ></div>
                  ) : null}
                </div>

                {/* Horixontal Line */}
                {index < steps.length - 1 && (
                  <div
                    className={`
                                    w-60 h-2 transition-all duration-900
                                    ${
                                      index < currentStep - 1
                                        ? "bg-blue-600"
                                        : index === currentStep - 1
                                        ? "bg-blue-600 animate-pulse"
                                        : "bg-gray-700 animate-pulse"
                                    }
                                `}
                  />
                )}
              </div>
              {/* Texts */}
              <div className="">
                <div
                  className={`font-bold text-left pt-5 text-lg transition-colors duration-900
                                    ${
                                      index === currentStep
                                        ? "text-blue-400"
                                        : index < currentStep
                                        ? "text-white"
                                        : "text-gray-500 animate-pulse"
                                    }`}
                >
                  {step.label}
                </div>
              </div>

              <div
                className={`text-md transition-colors duration-900
                                ${
                                  index === currentStep
                                    ? "text-blue-300"
                                    : index < currentStep
                                    ? "text-gray-300"
                                    : "text-gray-600 animate-pulse hidden"
                                }`}
              >
                {step.description}
              </div>
            </div>
          ))}
        </div>
        {response && currentStep > 100 && (
          <>
            <div className="flex p-16 px-32 justify-between">
              <div className="flex justify-around">
                <p className="text-white font-bold text-3xl ">Total: </p>
                <p className="text-white font-lg px-2 text-3xl">
                  {response.total_jobs}{" "}
                </p>
              </div>
              <div className="flex ">
                <p className="text-white font-bold text-3xl">Success:</p>
                <p className="text-white font-lg px-2 text-3xl">
                  {response.successful_applications[0].length}{" "}
                </p>
              </div>
              <div className="flex ">
                <p className="text-white font-bold text-3xl">Failed: </p>
                <p className="text-white font-lg px-2 text-3xl">
                  {response.failed_applications[0].length}{" "}
                </p>
              </div>
            </div>
            <div>
              <a href="https://www.linkedin.com/my-items/saved-jobs/?cardType=APPLIED">
                <h1 className="text-white text-5xl text-center">
                  Track your application here
                </h1>
              </a>
            </div>
          </>
        )}
      </div>
    </>
  );
};

export default Apply;
