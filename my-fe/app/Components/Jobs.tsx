"use client"
import React, { useEffect, useRef, useState } from 'react';
import JobCards from './JobCards';
import {sendUrl} from '../utiles/agentsCall';
import CryptoJS from 'crypto-js';
import toast from 'react-hot-toast';
import { useRouter } from 'next/navigation';
import { API_URL } from '../utiles/api';

  const steps = [
    {
      label: "Process started",
      description: "Fetching relevant Job Titles",
      min:0
    },
    {
      label: "Job Titles found!",
      description: "10%",
      min:10
    },
    {
      label: "Getting Jobs from server",
      description: "40%",
      min:20
    },
    {
      label: "Processing Jobs",
      description: "85%",
      min:85
    },
    {
      label: "Select the Jobs to apply!",
      description: "100%",
      min:100
    }
  ];

const Jobs = () => {

  const intervalRef = useRef<number | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [jobs, setJobs] = useState<any>();
  const [url, setUrl] = useState<string>("");
  const [userId, setUserId]  =useState<string>("")
  const [password, setPassword] = useState<string>("")
  const router = useRouter()

  // let jwt=""

  const ENC_KEY = "qwertyuioplkjhgfdsazxcvbnm987456" // ensure 32 bytes for AES-256
  const IV = "741852963qwerty0"

  function decryptData(ciphertextBase64: string, keyStr: string, ivStr: string) {
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
    const pdf = sessionStorage.getItem("resume")
    if(pdf)
      setUrl(pdf)
    else{
      toast.error("Resume not found. Please upload your resume")
      router.push("/Jobs/LinkedinUserDetails")
    }
    async function fetchEncryptedCredentials() {
      try {
  const res = await fetch("/api/get-data", {
          method: "GET",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        });

        const json = await res.json();
        // jwt=json.encryptedData as string

        if (json.encryptedData) {
          const decrypted = decryptData(json.encryptedData, ENC_KEY, IV);
          const credentials = JSON.parse(decrypted);
          setUserId(credentials.username);
          setPassword(credentials.password);
          // console.log("Decrypted user credentials:", userId," ",password);
        } else {
          // console.error("No encryptedData in response");
          toast.error("Linkedin credentials not provided")
          router.push("/Jobs/LinkedinUserDetails")
        }
      } catch (error:any) {
        // console.error("Error fetching or decrypting credentials:", error);
        toast.error("Error caused by: ",error.message)
      }
    }

    fetchEncryptedCredentials();
  }, []);

  // console.log("encrypted data: ", jwt)
  
  useEffect(()=>{
    const fetchJobs = async()=>{
      if(url==="" &&  userId==="" && password===""){
        // console.log("all parameters are empty")

        return
      }else if(userId===""){
        // console.log("userid is empty")
        return
      }
      else if(password===""){
        // console.log("password is empty")
        return
      }
      else if(url === ""){
        // console.log("file url is empty")
        return
      }
      else{
        // console.log("calling agent to fetch jobs");
        const {data ,error} = await sendUrl(url,userId,password)
        if(data)
          setJobs(data.jobs)
        else
          toast.error(`Error from fetching jobs ${error}`)
          // console.log("error from fetching jobs ",error);

      }
    }

    fetchJobs()
    if(userId)
    {
      intervalRef.current = window.setInterval(()=>{
  fetch(`${API_URL}/jobs/${userId}/progress`)
    .then((res)=>res.json())
    .then((data)=>{
      // console.log("progress: ",data.progress);
      // setPercentage(data.progress)
      let stepIndex=0
      for (let i = 0; i < steps.length; i++) {
          if (data.progress == 100){
            stepIndex = 110
          }
          else if (data.progress >= steps[i].min) {
            stepIndex = i;
          } 
          else {
            break;
          }
        }
        setCurrentStep(stepIndex)
        if (data.progress >= 100 && intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
    })
    },10000)
    return() => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
    }
    else{
      // console.log("user id not provided");
      
    }

  },[userId,password])

 

// console.log("current step: ",currentStep); 
// console.log("jwt:",jwt);
 

  return (
    <div className='flex flex-col lg:flex-row jobs-section min-h-screen'>
      <div className='flex flex-col gap-0 bg-gradient-to-b from-[#244283] to-[#0e3661] p-4 md:p-6 lg:p-8 py-8 lg:py-20 shadow-lg shadow-[#052718]-500 w-full lg:w-auto lg:max-w-xs lg:sticky lg:top-15 lg:left-0 lg:h-screen rounded-b-lg lg:rounded-r-lg lg:rounded-b-none cursor-default'>
        {steps.map((step, index) => (
          <div className="flex items-start" key={step.label}>
            {/* Connector Line & Circle Col */}
            <div className="flex flex-col items-center mr-3 md:mr-4 h-fit">
              {/* Circle */}
              <div
                className={`
                  w-5 h-5 md:w-6 md:h-6 rounded-full border-2 flex items-center justify-center transition-all duration-900 
                  ${
                    index < currentStep
                      ? "bg-[#1ab5a9] border-[#1ab5a9]"
                      : index === currentStep
                      ? "border-[#1ab5a9] bg-white animate-bounce"
                      : "border-gray-600 bg-[#13182c] animate-pulse"
                  }
                `}
              >
                {index < currentStep ? (
                  <svg className="w-2.5 h-2.5 md:w-3 md:h-3" viewBox="0 0 11 11"><circle cx="5.5" cy="5.5" r="5" fill="#fff" /></svg>
                ) : index === currentStep ? (
                  <div className="w-3 h-3 md:w-3.5 md:h-3.5 rounded-full bg-[#1ab5a9] animate-spin" />
                ) : null}
              </div>
              {/* Vertical Line */}
              {index < steps.length - 1 && (
                <div
                  className={`
                    w-0.5 md:w-1 h-8 md:h-10 pt-8 md:pt-14 transition-all duration-900
                    ${
                      index < currentStep - 1
                        ? "bg-[#1ab5a9]"
                        : index === currentStep - 1
                        ? "bg-[#0f766e] animate-pulse"
                        : "bg-gray-700 animate-pulse"
                    }
                  `}
                />
              )}
            </div>
            {/* Texts */}
            <div className="pb-2 md:pb-2">
              <div
                className={`font-bold text-sm md:text-base transition-colors duration-900
                  ${index === currentStep
                    ? "text-blue-400"
                    : index < currentStep
                    ? "text-white"
                    : "text-gray-500 animate-pulse"
                  }`}
              >
                {step.label}
              </div>
              <div
                className={`text-xs md:text-sm transition-colors duration-900
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
          </div>
        ))}
      </div>
      <div className='w-full h-auto p-4 md:p-6 lg:p-8'>
        {currentStep>100 ?
          (<JobCards jobs={jobs}/>):
          (
          <span className="flex items-center justify-center min-h-[60vh] lg:min-h-[80vh] text-white gap-2 flex-col">
            <svg
              className="animate-spin h-8 w-8 md:h-10 md:w-10 text-white"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="2"
                fill="black"
              />
              <path
                className="opacity-85"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
              />
            </svg>
            <p className="text-sm md:text-base">loading jobs... </p>
          </span>
          )
        }
      </div>
    </div>
  );
};

export default Jobs;
