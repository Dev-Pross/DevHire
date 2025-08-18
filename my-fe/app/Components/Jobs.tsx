import React, { useEffect, useRef, useState } from 'react';
import JobCards from './JobCards';

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


  useEffect(()=>{
    intervalRef.current = window.setInterval(()=>{
    fetch("http://127.0.0.1:8000/jobs/tejabudumuru3@gmail.com/progress")
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
  },[])

console.log("current step: ",currentStep);


  

  return (
    <div className='flex'>
      <div className='flex flex-col gap-0 bg-[#052718] p-8 py-20 shadow-lg shadow-[#052718]-500 w-full max-w-xs size-max sticky top-15 left-0 h-screen rounded-r-lg'>
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
                  <svg width="10" height="10"><circle cx="5" cy="5" r="5" fill="#fff" /></svg>
                ) : index === currentStep ? (
                  <div className="w-3 h-3 rounded-full bg-blue-400" />
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
      <div className='left-0 w-full'>
        {/* Right content */}
        <JobCards/>
      </div>
    </div>
  );
};

export default Jobs;
