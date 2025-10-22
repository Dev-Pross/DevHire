"use client";
import React, { useEffect, useRef, useState } from "react";
import { Apply_Jobs } from "../utiles/agentsCall";
import CryptoJS from "crypto-js";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";

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
  const router = useRouter();

  const [url, setUrl] = useState<string>("");
  const [userId, setUserId] = useState<string>("");
  const [password, setPassword] = useState<string>("");

  const [user, setUser] = useState<string | null>(null);
  const [dbData, setDbData] = useState<any>();

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
  //  fetching resume, li_c, jobs, id, applied jobs
  useEffect(() => {
    // fecthing resume
    const pdf = sessionStorage.getItem("resume");
    if (pdf) setUrl(pdf);
    else {
      toast.error("Resume not found. Please upload your resume")
      router.push("/Jobs/LinkedinUserDetails")
    }

    // fecthing jobs, user id
    const job_data = sessionStorage.getItem("jobs");
    const id = sessionStorage.getItem("id");
    if (job_data != null) {
      setJobs(JSON.parse(job_data));
    } else {
      toast.error("No jobs found to proceed")
      router.push("/Jobs")
    }
    if (id != null) {
      setUser(id);
    } else {
      // throw new Error("no id found");
      toast.error("Please Login to start")
    }

    // console.log("jobs from ls: ", job_data);

    // fetching li_c
    async function fetchEncryptedCredentials() {
      try {
        const res = await fetch("https://dev-hire-znlr.vercel.app/api/get-data", {
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
        } else {
          // console.error("No encryptedData in response");
          toast.error("Linkedin credentials not provided")
          router.push("/Jobs/LinkedinUserDetails")
        }
      } catch (error: any) {
        // console.error("Error fetching or decrypting credentials:", error);
        toast.error("Error caused by: ", error.message)
      }
    }

    fetchEncryptedCredentials();

    // fecthing applied jobs from database
    async function getAppliedJobs() {
      const res = await fetch(`/api/User?id=${user}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });
      const my_data = await res.json();
      if (res) {
        // console.log("mydata", my_data.user.applied_jobs);
        setDbData(my_data.user.applied_jobs);
      }
    }
    if (user) getAppliedJobs();
  }, [user, router]);

  // Applying jobs
  useEffect(() => {
    // console.log("apply called");
    // console.log("Ready to apply: ", { jobs, userId, dbData });
    if (!jobs || jobs.length === 0) return;
    if (!user) return;
    if (!dbData) return;
    if (!userId) return;

    async function apply() {
      try {
        const { data, error } = await Apply_Jobs(jobs, url, userId, password);
        if (data) {
          sessionStorage.setItem("applied", data.successful_applications.flat(Infinity).length)
          const payload = [
            ...new Set([
              ...dbData,
              ...data.successful_applications.flat(Infinity),
            ]),
          ];
          const res = await fetch("/api/User?action=update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              id: user,
              data: { column: "applied_jobs", value: payload },
            }),
          });
          // console.log(user);

          if (res.ok) {
            console.log("data pushed");
          } else {
            console.log("data pushed failed");
          }
          setResponse(data);
        } else {
          // console.log("error from fetching jobs ", error?.status);
          toast.error("Error from fetching jobs: ", error?.status)
          if (error.status === 500) {
            // console.log("cant reach server, please try again");
            toast.error("Can't reach server, please try again")
          }
        }
      } catch (error: any) {
        toast.error("Error in applying jobs ", error.message);

      }
    }

    apply();

    if (userId) {
      // console.log("all set to start apply");

      intervalRef.current = window.setInterval(() => {
        fetch(`http://127.0.0.1:8000/apply/${userId}/progress`)
          .then((res) => res.json())
          .then((data) => {
            // console.log("progress: ", data.progress);
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
      toast.error("Linkedin credentials not provided")
      router.push("/Jobs/LinkedinUserDetails")
    }
  }, [user, jobs, dbData]);

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
                              ${index < currentStep
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
                              ${index < currentStep - 1
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
                              ${index === currentStep
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
                            ${index === currentStep
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
                  {response.successful_applications.flat(Infinity).length}{" "}
                </p>
              </div>
              <div className="flex ">
                <p className="text-white font-bold text-3xl">Failed: </p>
                <p className="text-white font-lg px-2 text-3xl">
                  {response.failed_applications.flat(Infinity).length}{" "}
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
