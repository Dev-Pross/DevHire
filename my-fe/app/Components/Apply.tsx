
"use client"
import React, { useEffect, useRef, useState } from 'react'
import { Apply_Jobs } from '../utiles/agentsCall';

    interface jobsData{
    "job_url":string,
    "job_description":string
    }

    interface ApplyProps {
        url?: string;
        userId?: string;
        password?: string;
        jobs?: jobsData[];
    }



const Apply : React.FC<ApplyProps> = () => {
    
    const steps = [
    {
      label: "Processing jobs",
      description: "1%",
      min:0
    },
    {
      label: "Talioring Resume",
      description: "10%",
      min:10
    },
    {
      label: "Proccessing Resumes",
      description: "40%",
      min:20
    },
    {
      label: "Applying Jobs",
      description: "85%",
      min:85
    },
    {
      label: "Applied Successfully",
      description: "100%",
      min:100
    }
  ];
    const intervalRef = useRef<number | null>(null);
    const [currentStep, setCurrentStep] = useState(0);
    const [response, setResponse] = useState<any>(null)
    
    const url="https://uunldfxygooitgmgtcis.supabase.co/storage/v1/object/sign/user-resume/SRINIVAS_SAI_SARAN_TEJA%20(1).pdf?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9iZjI4OTBiZS0wYmYxLTRmNTUtOTI3Mi0xZGNiNTRmNzNhYzAiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJ1c2VyLXJlc3VtZS9TUklOSVZBU19TQUlfU0FSQU5fVEVKQSAoMSkucGRmIiwiaWF0IjoxNzU0Mzc4OTgwLCJleHAiOjE3NTY5NzA5ODB9.1unaMom_BGXfxkvFB95XUMFLw7FOoVzMDBwzrJI8mOs"
    const userId="linkedinpostgenerator@gmail.com"
    const password="mDEccH86!zmGr:_"
    const jobs=
        [
    {
        "job_description": "About the job\n\nWe have a Three different position for JAVA,\n\n\n\n\n* Java Backend Developer (Spring, Spring Boot, Microservices,)\n\n* Java Developer with DevOps (Docker / Kubernetes / Jenkins )\n\n* Java Developer with AWS\n\n \n\nDrive Date :- 23rd Aug\n\nTiming :- 9.30am to 4.30pm\n\n\n\n\nF2F Drive Venue:\n\nHyderabad \nChennai",
        "job_url": "https://in.linkedin.com/jobs/view/4289023423/"
    },
    {
        "job_description": "About the job\n\nCompany Description\n\nTeknikforce Ventures LLC is a rapidly growing creator of innovative digital marketing tools designed for digital marketers and small business owners. We develop both web-based and desktop-based software to enhance efficiency and productivity. Teknikforce leverages cutting-edge technologies to deliver high-quality software applications and websites. The company embraces a work-from-home culture, with employees spread across the globe. Teknikforce has created more than 20 exceptional digital marketing tools, continually innovating and improving in technology, customer service, product delivery, marketing, and work environments.\n\n\n\n\nRole Description\n\nThis is a full-time remote role for a Junior JavaScript/Node JS Developer. The Junior Developer will be responsible for contributing to both front-end and back-end web development tasks, assisting in the full software development lifecycle. Daily tasks include writing and maintaining code in JavaScript, collaborating with the development team, and ensuring that applications are user-friendly and efficient. \n\n\n\n\nQualifications\n\nFront-End Development skills\nBack-End Web Development skills\nKnowledge of JavaScript and Node.js\nStrong Software Development skills\nExcellent problem-solving and analytical skills\nAbility to work independently and remotely\nFreshers can also apply if you have strong skills",
        "job_url": "https://in.linkedin.com/jobs/view/4286717972/"
    },
    {
        "job_description": "About the job\n\nCompany Description\n\nVrozart Group is a progressive organization with diverse interests in healthcare, financial services, agriculture, digital technologies, and media & entertainment. The company aims to generate wealth, prosperity, and progress for its stakeholders by empowering entrepreneurs with opportunities, resources, and knowledge for their growth and success. With a vision to become the most trusted organization, Vrozart impacts millions of lives across India through its extensive network and the brand Vrozart.\n\n\n\n\nRole Description\n\nThis is a full-time on-site role for a Python Developer with minimum experience of 2 years ,located in the Mohali district . The Python Developer will be responsible for back-end web development, creating and maintaining software applications, implementing object-oriented programming (OOP) principles, programming, and managing databases. The role involves collaborating with cross-functional teams, ensuring timely delivery of projects, and troubleshooting issues that arise during development.\n\n\n\n\nQualifications\n\nProficiency in Back-End Web Development and Software Development\nStrong understanding of Object-Oriented Programming (OOP) and Programming\nExperience with Databases management\nExcellent problem-solving and analytical skills\nAbility to work collaboratively with cross-functional teams\nRelevant experience in the software development industry\nBachelor's degree in Computer Science, Software Engineering, or a related field",
        "job_url": "https://in.linkedin.com/jobs/view/4289024904/"
    },
    {
        "job_description": "About the job\n\nCompany Description\n \nWe suggest you enter details here.\n\n Role Description\n \nThis is a full-time on-site role for a Technical Engineer, located in Jodhpur. The Technical Engineer will be responsible for installing, maintaining, and troubleshooting technical systems and equipment. Day-to-day tasks include performing system diagnostics, providing technical support to staff and clients, and implementing technical improvements. The role also involves collaborating with cross-functional teams to address technical issues and ensure the efficient operation of systems.\n\n Qualifications\n \n\nTechnical system installation and maintenance skills\nStrong diagnostic and troubleshooting skills\nTechnical support and customer service skills\nExperience with system improvements and upgrades\nExcellent problem-solving and analytical thinking skills\nStrong written and verbal communication skills\nAbility to work collaboratively in a team environment\nBachelor's degree in Engineering, Information Technology, or a related field",
        "job_url": "https://in.linkedin.com/jobs/view/4286715490/"
    },
    {
        "job_description": "About the job\n\nCompany Description\n\n \n\nLinovate Solutions is a premier IT service provider based in Dubai, established in 2019. We specialize in a comprehensive range of services, including software development, ERP systems, website and e-commerce development, fleet management systems, digital marketing, branding, and business consulting. Our mission is to empower businesses with innovative IT solutions that drive growth and efficiency.\n\n\n\n\nWith a dedicated team of experts, we have successfully completed over 500 projects across the UAE and 20 countries, serving government entities, semi-government organizations, corporates, and SMEs. Our commitment to excellence and customer satisfaction sets us apart in the competitive landscape of IT services.\n\n\n\n\n Role Description\n\n \n\nThis is a full-time on-site role for an Odoo Developer located in Kozhikode. The Odoo Developer will be responsible for developing, testing, and maintaining custom modules in Odoo. Daily tasks will include back-end web development, software development, and programming using Odoo's framework. The developer will also troubleshoot and debug applications, as well as collaborate with cross-functional teams to ensure smooth integration of software solutions. In this role, staying updated with the latest Odoo versions and features is essential.\n\n\n\n\n Qualifications\n\n \n\nStrong foundation in Computer Science\nExperience in Back-End Web Development and Software Development\nProficient in Programming and Object-Oriented Programming (OOP)\nExcellent analytical and problem-solving skills\nAbility to work collaboratively in a team environment\nPrior experience with Odoo or similar ERP systems is a plus\nBachelor's degree in Computer Science, Information Technology, or a related field",
        "job_url": "https://in.linkedin.com/jobs/view/4286726631/"
    }
]
    


  useEffect(()=>{
    async function apply(){
        const {data,error} = await Apply_Jobs(jobs,url,userId,password)
        if(data)
          setResponse(data)
        else
          console.log("error from fetching jobs ",error);
    }

    apply()

    if(userId)
    {
      intervalRef.current = window.setInterval(()=>{
    fetch(`http://127.0.0.1:8000/apply/${userId}/progress`)
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
    },2000)
    return() => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
    }
    else{
      console.log("user id not provided");
      
    }

  },[])

  console.log("apply server output ",response);
  

  return (
    <>
        <div className='h-screen'>
            <div className='flex justify-center gap-0 bg-transparent p-18 py-20 shadow-lg shadow-[#052718]-500 w-full max-w-screen sticky top-15 mt-10  rounded-r-lg cursor-default'>
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
                                        ? "border-blue-500  shadow-white-500 bg-white "
                                        : "border-gray-600 bg-[#13182c] animate-pulse"
                                    }
                                    `}
                                    >
                                    {index < currentStep ? (
                                    <svg width="30" height="30"><circle cx="15" cy="15" r="14" fill='#fff'/></svg>
                                    ) : index === currentStep ? (
                                        
                                    // <div className="w-3 h-10 rounded-full bg-blue-400 animate-spin" />
                                    <div className={`bg-[url('/spinner.svg')] w-15 h-15 bg-no-repeat`}></div>
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
            {
            (response && currentStep>100) && 
            <>
                <div className='flex p-16 px-32 justify-between'>
                    <div className='flex justify-around'>
                        <p className='text-white font-bold text-3xl '>Total: </p>
                        <p className='text-white font-lg px-2 text-3xl'>{response.total_jobs} </p>
                    </div>
                    <div className='flex '>
                        <p className='text-white font-bold text-3xl'>Success:</p>
                        <p className='text-white font-lg px-2 text-3xl'>{response.successful_applications} </p>
                    </div>
                    <div className='flex '>
                        <p className='text-white font-bold text-3xl'>Failed: </p>
                        <p className='text-white font-lg px-2 text-3xl'>{response.failed_applications} </p>
                    </div>
                </div>
                <div>
                    <a href='https://www.linkedin.com/my-items/saved-jobs/?cardType=APPLIED'><h1 className='text-white text-5xl text-center'>Track your application here</h1></a>
                </div>
            </>
            }
        </div>
    </>
  )
}

export default Apply