"use client"
import React, { useEffect, useRef, useState } from 'react';
import JobCards from './JobCards';
import {sendUrl} from '../utiles/agentsCall';
import CryptoJS from 'crypto-js';

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


  let jwt=""

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
      

    async function fetchEncryptedCredentials() {
      try {
        const res = await fetch("http://localhost:3000/api/get-data", {
          method: "GET",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        });

        const json = await res.json();
        jwt=json.encryptedData as string

        if (json.encryptedData) {
          const decrypted = decryptData(json.encryptedData, ENC_KEY, IV);
          const credentials = JSON.parse(decrypted);
          setUserId(credentials.username);
          setPassword(credentials.password);
          console.log("Decrypted user credentials:", userId," ",password);
        } else {
          console.error("No encryptedData in response");
        }
      } catch (error) {
        console.error("Error fetching or decrypting credentials:", error);
      }
    }

    fetchEncryptedCredentials();
  }, []);

  console.log("encrypted data: ", jwt)
  
  useEffect(()=>{
    const fetchJobs = async()=>{
      if(url==="" &&  userId==="" && password===""){
        console.log("all parameters are empty")
        return
      }else if(userId===""){
        console.log("userid is empty")
        return
      }
      else if(password===""){
        console.log("password is empty")
        return
      }
      else if(url === ""){
        console.log("file url is empty")
        return
      }
      else{
        console.log("calling agent to fetch jobs");
        const {data ,error} = await sendUrl(url,userId,password)
        if(data)
          setJobs(data.jobs)
        else
          console.log("error from fetching jobs ",error);
      }
    }

    fetchJobs()
    if(userId)
    {
      intervalRef.current = window.setInterval(()=>{
    fetch(`http://127.0.0.1:8000/jobs/${userId}/progress`)
    .then((res)=>res.json())
    .then((data)=>{
      console.log("progress: ",data.progress);
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
      console.log("user id not provided");
      
    }

  },[userId,password])

 

console.log("current step: ",currentStep); 
console.log("jwt:",jwt);
 

  return (
    <div className='flex'>
      <div className='flex flex-col gap-0 bg-[#052718] p-8 py-20 shadow-lg shadow-[#052718]-500 w-full max-w-xs size-max sticky top-15 left-0 h-screen rounded-r-lg cursor-default'>
        {steps.map((step, index) => (
          <div className="flex items-start" key={step.label}>
            {/* Connector Line & Circle Col */}
            <div className="flex flex-col items-center mr-4 h-fit">
              {/* Circle */}
              <div
                className={`
                  w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all duration-900 
                  ${
                    index < currentStep
                      ? "bg-blue-600 border-blue-600"
                      : index === currentStep
                      ? "border-blue-500 bg-white animate-bounce"
                      : "border-gray-600 bg-[#13182c] animate-pulse"
                  }
                `}
              >
                {index < currentStep ? (
                  <svg width="10" height="10"><circle cx="5.5" cy="5" r="5" fill="#fff" /></svg>
                ) : index === currentStep ? (
                  <div className="w-3 h-3 rounded-full bg-blue-400 animate-spin" />
                ) : null}
              </div>
              {/* Vertical Line */}
              {index < steps.length - 1 && (
                <div
                  className={`
                    w-1 h-10 pt-14 transition-all duration-900
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
            <div className="pb-8">
              <div
                className={`font-bold text-base transition-colors duration-900
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
                className={`text-sm transition-colors duration-900
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
      <div className='right-15 '>
        {currentStep>100 &&
          <JobCards jobs={jobs}/>
        }
      </div>
    </div>
  );
};

export default Jobs;
