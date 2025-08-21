import React from 'react'

const Apply = ({currentStep = 3}) => {
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
  return (
    <>
        <div className=''>
            <div className='flex justify-center gap-0 bg-transparent p-8 py-20 shadow-lg shadow-[#052718]-500 w-full max-w-screen sticky top-15   rounded-r-lg cursor-default'>
                {
                    steps.map((step,index)=>(
                        <div className='flex flex-col item-start' key={step.label}>
                            <div className="flex  items-center mr-1 h-fit">
                                <div
                                    className={`
                                    w-15 h-15 rounded-full border-2 flex items-center justify-center transition-all duration-900 
                                    ${
                                        index < currentStep
                                        ? "bg-blue-600 border-blue-600"
                                        : index === currentStep
                                        ? "border-blue-500 motion-safe:animate-spin shadow-white-500 bg-white "
                                        : "border-gray-600 bg-[#13182c] animate-pulse"
                                    }
                                    `}
                                    >
                                    {index < currentStep ? (
                                    <svg width="30" height="30"><circle cx="15" cy="15" r="14" fill="#fff" /></svg>
                                    ) : index === currentStep ? (
                                    <div className="w-3 h-10 rounded-full bg-blue-400" />
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
                        
                    ))
                }
            </div>

        </div>
    </>
  )
}

export default Apply