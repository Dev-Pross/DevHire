"use client"

import { useRouter } from 'next/navigation';
import React, { useState } from 'react'

interface JobcardProps{
    title:string,
    job_id:string,
    company_name:string,
    location:string,
    experience:string,
    salary:string,
    key_skills:string[],
    job_url:string,
    posted_at:string,
    job_description:string,
    source:string,
    relevance_score:string,
}

interface JobCardsProps{
    jobs:JobcardProps[];
}
// const jobs=[
//     {
//     "title": "Software Engineer",
//     "job_id": "4292603957",
//     "company_name": "AAPMOR",
//     "location": "Hyderabad",
//     "experience": null,
//     "salary": null,
//     "key_skills": [
//       "Java",
//       "Python",
//       "C++",
//       "Agile",
//       "Scrum",
//       "HTML",
//       "CSS",
//       "JavaScript",
//       "SQL",
//       "NoSQL",
//       "Problem-solving",
//       "Analytical skills"
//     ],
//     "job_url": "https://in.linkedin.com/jobs/view/4292603957/",
//     "posted_at": null,
//     "job_description": "About the job\n\nCompany Description\n \n\nAAPMOR is a leading provider of Automation and AI solutions. Our mission is to revolutionize the way businesses approach digital transformation by empowering them with the tools and expertise they need to thrive in today’s fast-paced and ever-changing digital landscape. With a focus on innovation and excellence, AAPMOR aims to deliver cutting-edge technology solutions that enable businesses to achieve operational efficiency and scalability.\n\n\n Role Description\n \n\nThis is a full-time on-site role for a Software Engineer, located in Hyderabad. The Software Engineer will be responsible for designing, developing, and implementing software solutions to meet the needs of our clients. Tasks include coding, debugging, and testing new software applications, as well as maintaining and improving existing applications. The role may also involve collaborating with cross-functional teams to understand requirements and providing technical support and documentation.\n\n\n Qualifications\n \nProficiency in programming languages such as Java, Python, or C++\nExperience with software development methodologies like Agile and Scrum\nKnowledge of web technologies including HTML, CSS, and JavaScript\nFamiliarity with database management systems such as SQL and NoSQL\nStrong problem-solving and analytical skills\nExcellent written and verbal communication skills\nAbility to work collaboratively in a team environment\nBachelor's degree in Computer Scie",
//     "source": "linkedin",
//     "relevance_score": null
//   },
//   {
//     "title": "Python Backend Developer + AWS",
//     "job_id": "4292834193",
//     "company_name": "MyRemoteTeam, Inc",
//     "location": "Any Infosys DC",
//     "experience": "8+ Yrs",
//     "salary": null,
//     "key_skills": [
//       "Python",
//       "AWS Lamda",
//       "Micro services",
//       "Graph QL",
//       "SQL acchemy",
//       "GIT",
//       "AWS Lambda",
//       "PostgreSQL",
//       "object-oriented concepts",
//       "design patterns",
//       "ORM tools",
//       "SQLAlchemy",
//       "GraphQL APIs",
//       "SCRUM",
//       "branching strategies"
//     ],
//     "job_url": "https://in.linkedin.com/jobs/view/4292834193/",
//     "posted_at": null,
//     "job_description": "About the job\n\nAbout Us\n\nMyRemoteTeam, Inc is a fast-growing distributed workforce enabler, helping companies scale with top global talent. We empower businesses by providing world-class software engineers, operations support, and infrastructure to help them grow faster and better.\n\n\n\n\nJob Title: Python Backend Developer + AWS\n\nExp: 8+ Yrs\n\nLocation: Any Infosys DC\n\nMandatory Skills: Python, AWS Lamda, Micro services, Graph QL, SQL acchemy, GIT\n\n\n\n\n\n\n\n7+ years of experience in application development using Python, AWS Lambda, microservices architecture, and PostgreSQL.\nAdvanced proficiency in Python programming, object-oriented concepts, and design patterns.\nStrong hands-on expertise with ORM tools, especially SQLAlchemy.\nExperience building and integrating GraphQL APIs.\nProven track record working in SCRUM teams, utilizing GIT and branching strategies for collaborative development.",
//     "source": null,
//     "relevance_score": null
//   },
//   {
//     "title": "Odoo Developer",
//     "job_id": "4292471795",
//     "company_name": "SDK Infinity",
//     "location": "Chennai",
//     "experience": "1 to 3 Years",
//     "salary": null,
//     "key_skills": [
//       "Computer Science",
//       "Software Development",
//       "Programming",
//       "Odoo Implementation",
//       "Odoo Development",
//       "Back-End Web Development",
//       "Object-Oriented Programming (OOP)",
//       "Odoo development framework",
//       "modular architecture",
//       "problem-solving",
//       "analytical skills",
//       "database management",
//       "version control systems"
//     ],
//     "job_url": "https://in.linkedin.com/jobs/view/4292471795/",
//     "posted_at": null,
//     "job_description": "About the job\n\nCompany Description\n\nSDK Infinity is an Odoo Ready Certified Partner with a dedicated team of functional consultants and technical developers. We specialize in providing tailored Odoo solutions to meet diverse business requirements. Our team is committed to delivering high-quality and efficient solutions to help businesses streamline their operations and enhance productivity.\n\n\n\n\nRole Description\n\nThis is a full-time on-site role for an Odoo Developer located in Chennai. The Odoo Developer will be responsible for developing and maintaining custom Odoo modules, configuring Odoo applications, and providing technical support to clients. Day-to-day tasks include coding, debugging, and collaborating with functional consultants to design and implement features that meet client needs. The developer will also participate in code reviews, ensure compliance with coding standards, and contribute to continuous improvement efforts.\n\n\n\n\nQualifications\n\nComputer Science, Software Development, and Programming skills\n1 to 3 Years of Hands-on experience in Odoo Implementation & Development\nBack-End Web Development and Object-Oriented Programming (OOP) skills\nStrong understanding of Odoo development framework and modular architecture\nExcellent problem-solving and analytical skills\nAbility to work collaboratively in a team environment\nBachelor’s degree in Computer Science or a related field\nExperience in database management and version control systems is a",
//     "source": null,
//     "relevance_score": null
//   },
//   {
//     "title": "Azure DevOps/Infra Developer/Associate",
//     "job_id": "4292529267",
//     "company_name": null,
//     "location": null,
//     "experience": null,
//     "salary": null,
//     "key_skills": [
//       "Azure DevOps",
//       "Azure infrastructure",
//       "Role-Based Access Control (RBAC)",
//       "scalability",
//       "monitoring",
//       "cost management",
//       "Azure services",
//       "DevOps methodologies",
//       "Resource Monitoring",
//       "Logging",
//       "Telemetry",
//       "alerts",
//       "Performance Optimization"
//     ],
//     "job_url": "https://in.linkedin.com/jobs/view/4292529267/",
//     "posted_at": null,
//     "job_description": "About the job\n\nJob Description: Azure DevOps/Infra Developer/Associate\n\nWe are seeking a skilled Azure DevOps/Infra Developer/Associate to join our team. The ideal candidate will be responsible for managing and optimizing our Azure infrastructure, ensuring robust role-based access control (RBAC), and implementing best practices for scalability, monitoring, and cost management. This is a hands-on role requiring expertise in Azure services and DevOps methodologies, with a focus on immediate tasks related to infrastructure setup, monitoring, and optimisation.\n\n\n\n\nKey Responsibilities:\n\nRBAC/User Management:\n\nDesign and implement robust Role-Based Access Control (RBAC) policies.\nSet up and manage users and groups to ensure secure access to Azure resources.\n\n\n\nResource Monitoring:\n\nCreate dashboards to monitor performance and utilization of different Azure resources.\nEnsure dashboards provide actionable insights into infrastructure health and performance.\n\n\n\n\nTechnical Leadership:\n\nEstablish and promote best practices for Azure infrastructure and DevOps processes.\nProvide guidance and mentorship to team members on Azure and DevOps-related topics.\n\n\n\n\nLogging and Telemetry:\n\nImplement centralized logging and telemetry solutions.\nSet up alerts to proactively monitor for potential issues and resolve them promptly.\n\n\n\n\nScalability and Performance Optimization:\n\nArchitect and implement scalable solutions to handle increasing workloads.\nOptim",
//     "source": null,
//     "relevance_score": null
//   },
//   {
//     "title": "Dev Studio (Majesco) Developer",
//     "job_id": "4290726440",
//     "company_name": "PM AM",
//     "location": "Permanent Remote",
//     "experience": null,
//     "salary": null,
//     "key_skills": [
//       "Majesco Dev-Studio framework",
//       "PlSql Concepts",
//       "debugging",
//       "Agile SDLC"
//     ],
//     "job_url": "https://in.linkedin.com/jobs/view/4290726440/",
//     "posted_at": null,
//     "job_description": "About the job\n\nCompany Description\n\nPM AM is a 25-year-old product & Service software company with offices in Dallas, Houston, and Mumbai. We work with over 500 clients across the Government, US P&C Insurance, and Retail sectors. Our AI and automation platforms have been widely recognized—including a mention from Intel’s CEO and an award from UI Path for our RPA solutions. We are dedicated to serving customers around the clock, specializing in False Alarm Management, Human Capital Management, Customer Relationship Management, and Offshore Software Development. Our commitment lies in reducing customer costs, providing world-class customer service, and maintaining corporate social responsibility. We serve a diverse range of customers in both the government and private sectors.\n\n \n\n\n\n\nWe are Hiring Dev Studio (Majesco) Developer - Permanent Remote.\n\nPreferred - immediate joiner\n\n\n\n\nRequirements\n\nCandidate having hands on experience in developing insurance solution using Majesco Dev-Studio framework.\nShould have good knowledge on PlSql Concepts.\nAbility to debug the application using debug panel or other debugger techniques in Majesco products / PlSql.\nAddressing the defects and Change requests and working closely with testing team and implementing the requirements.\nHaving good understanding of Insurance concepts and work streams.\nPreferably worked on Agile SDLC delivery model.",
//     "source": null,
//     "relevance_score": null
//   },
//   {
//     "title": "Junior Backend Developer",
//     "job_id": "4292501468",
//     "company_name": null,
//     "location": "Hyderabad",
//     "experience": "1–2 years",
//     "salary": null,
//     "key_skills": [
//       "Go (Golang)",
//       "REST API design",
//       "REST API development",
//       "PostgreSQL",
//       "MySQL",
//       "MongoDB",
//       "Microsoft Azure",
//       "AWS",
//       "AI-powered developer tools",
//       "ChatGPT",
//       "Replit",
//       "Windsurf",
//       "Agile methodologies",
//       "SDLC workflows",
//       "enterprise-level backend systems",
//       "problem-solving",
//       "debugging",
//       "Node.js"
//     ],
//     "job_url": "https://in.linkedin.com/jobs/view/4292501468/",
//     "posted_at": null,
//     "job_description": "About the job\n\nRole: Junior Backend Developer\n\nLocation: Hyderabad\n\n \n\nRequired Skills:\n\n• 1–2 years of hands-on backend development experience\n\n• Proficiency in Go (Golang) is mandatory\n\n• Solid experience with REST API design and development\n\n• Strong command over PostgreSQL, MySQL, and MongoDB\n\n• Good understanding of Microsoft Azure or AWS (at least one is required)\n\n• Knowledge and usage of AI-powered developer tools like ChatGPT, Replit, Windsurf, or equivalents\n\n• Exposure to Agile methodologies and complete SDLC workflows\n\n• Hands-on experience working on enterprise-level backend systems\n\n• Excellent problem-solving skills, attention to detail, and strong debugging abilities\n\n• Bonus: Working knowledge of Node.js",
//     "source": null,
//     "relevance_score": null
//   },
//   {
//     "title": "Python Backend Developer",
//     "job_id": "4292399267",
//     "company_name": null,
//     "location": null,
//     "experience": null,
//     "salary": null,
//     "key_skills": [
//       "Python",
//       "object-oriented programming",
//       "data structures",
//       "algorithms",
//       "design patterns",
//       "Flask",
//       "FastAPI",
//       "Django",
//       "RESTful API design",
//       "RESTful API integration",
//       "Git",
//       "PostgreSQL",
//       "MySQL",
//       "MongoDB",
//       "unit testing",
//       "debugging tools",
//       "Docker",
//       "Kubernetes",
//       "AWS",
//       "Azure",
//       "CI/CD pipelines",
//       "DevOps principles",
//       "message queues",
//       "RabbitMQ",
//       "Kafka",
//       "automation",
//       "system integrations"
//     ],
//     "job_url": "https://in.linkedin.com/jobs/view/4292399267/",
//     "posted_at": null,
//     "job_description": "About the job\n\nKey Responsibilities:\n\n\n\n\n• Design, develop, and maintain efficient, reusable, and reliable Python code.\n\n• Build core backend services and APIs using Python.\n\n• Write clean, maintainable code following best practices and coding standards.\n\n• Work with cross-functional teams to define and implement new features.\n\n• Optimize applications for maximum speed and scalability.\n\n• Conduct unit testing and debugging to ensure high-quality software delivery\n\n• Maintain documentation and codebase as per development standards.\n\n• Collaborate with DevOps or QA teams for integration and deployment.\n\n\n\n\nRequired Skills:\n\n\n\n\n• Strong command of Core Python and object-oriented programming.\n\n• Solid understanding of data structures, algorithms, and design patterns.\n\n• Experience with any one or more Python frameworks like Flask, FastAPI, or Django.\n\n• Proficiency in RESTful API design and integration.\n\n• Familiarity with version control tools like Git.\n\n• Knowledge of databases such as PostgreSQL, MySQL, or MongoDB.\n\n• Exposure to unit testing and debugging tools.\n\n\n\n\nGood to Have:\n\n\n\n\n• Familiarity with Docker, Kubernetes, or cloud services like AWS or Azure.\n\n• Knowledge of CI/CD pipelines and DevOps principles.\n\n• Experience in working with message queues (RabbitMQ, Kafka).\n\n\n\n\n• Prior experience in building tools for automation or system integrations.",
//     "source": null,
//     "relevance_score": null
//   }
// ]

const JobCards: React.FC<JobCardsProps> = ({jobs=[] }) => {


    const router = useRouter()

    const [selectedIds, setSelectedIds] = useState<{job_id: string, job_url: string, job_description: string}[]>([])
    const selectAllHandler = ()=>{
        if (selectedIds.length == jobs.length){
            setSelectedIds([])
            return
        }
        const allIds = jobs.map(({job_id,job_description,job_url})=>({
            job_id,
            job_description,
            job_url
        }))
        console.log("all ids: ",allIds)
        setSelectedIds(allIds)
    }
    console.log("slect all",selectedIds);
    
   
    const ApplierHandler = ()=>{
        if(selectedIds.length === 0){
            console.log("please select jobs to proceed");
            return
        }
        else{
            console.log("data sending to apply agent...", selectedIds);
            const refinedJobs = selectedIds.map(({ job_url, job_description }) => ({
                job_url,
                job_description,
                }));

            sessionStorage.setItem("jobs",JSON.stringify(refinedJobs))
            router.push("/apply")
        }
        
    }
    
    
    
    const cardHandler = (e: React.MouseEvent<HTMLLabelElement>, job: {job_id: string, job_url:string, job_description:string}) => {
        e.preventDefault();

        setSelectedIds(prev => {
            const isSelected = prev.some(selectedJob => selectedJob.job_id === job.job_id);
            if (isSelected) {
            // Remove job from selection
            return prev.filter(selectedJob => selectedJob.job_id !== job.job_id);
            } else {
            // Add job to selection
            console.log("previos ",prev);
            // const previous = prev.map(j=>j.job_id,job.job_url,job.job_description)
            
            return [...prev, {job_url: job.job_url, job_id: job.job_id, job_description:job.job_description}];
            }
        });
    console.log(selectedIds.length);
  
    }
  return (
    <>
        <div className='w-full   p-4 flex justify-between items-center sticky top-15 backdrop-blur-xl z-5 '>
            <div className='flex px-5 items-center '>
                <p className='text-white font-sm font-light'>Selected jobs: {selectedIds.length}</p>
                <button className='text-white font-sm font-light p-5 rounded-2xl border-1 px-6 py-2 mx-3' onClick={selectAllHandler}>select all</button>
            </div>
            <div>
                <button className='rounded-2xl border-2 px-6 py-2 curser-pointer text-white hover:bg-black' onClick={ApplierHandler}>Apply all</button>
            </div>
            </div>
        <div className='flex flex-wrap w-full'>
        {jobs.map(job => (
            <label
                key={job.job_id}
                className={`m-5 ml-8 mr-8 ml-4 rounded-xl h-100 cursor-pointer min-w-sm max-w-sm bg-[#183b70] shadow-lg shadow-[#052718]-500 relative 
                            ${selectedIds.some(selectedJob => selectedJob.job_id === job.job_id) ? 'border border-white shadow-white/50' : 'border border-transparent'} `}
                onClick={(e) => cardHandler(e, { job_id: job.job_id, job_url: job.job_url, job_description: job.job_description })}
            >
                 
                <input
                type='checkbox'
                name="job_selector"
                className='sr-only'
                checked={selectedIds.includes({job_id:job.job_id,job_url:job.job_url,job_description:job.job_description})}
                onChange={()=>{}}
                />
                { job.title ? (
                <div className='flex flex-col px-10 py-5 justify-around'>
                    <div className='inline-flex justify-between'>
                        <p className='text-white hover:text-gray-100 font-light text-sm '>{job.company_name}</p>
                        <p className='text-white hover:text-gray-100 font-thin text-xs content-center'>{job.posted_at}</p>
                    </div>
                    
                        <a className='text-white hover:text-gray-100 font-bold text-xl' href={job.job_url} onClick={e => e.stopPropagation()} target='_blank'>{job.title}</a>
                        <p className='text-white hover:text-gray-100 font-thin text-sm'>{job.location}</p>
                </div>
                ) :  (<div className='flex flex-col px-10 py-5 justify-around'>
                    <div className='inline-flex justify-between'>
                        <p className='text-white hover:text-gray-100 font-light text-sm '>{job.company_name}</p>
                        <p className='text-white hover:text-gray-100 font-thin text-xs content-center'>{job.posted_at}</p>
                    </div>
                    
                        <a className='text-white hover:text-gray-100 font-bold text-xl' href={job.job_url} onClick={e => e.stopPropagation()}>Network error</a>
                        <p className='text-white hover:text-gray-100 font-thin text-sm'>{job.location}</p>
                </div>)}
                <div className='max-w-lg'>
                    <div className='flex p-2 flex-wrap'>
                        {job.key_skills.slice(0,6).map((skill,idx)=>(
                        <p className='px-4  rounded-full m-1 bg-gray-600 text-white font-thin' key={skill+idx}> {skill}</p>
                        ))}
                    </div>
                </div>
                <div className='flex justify-between p-4 bottom-0 absolute w-full'>
                    {job.relevance_score &&
                    <div className='flex flex-col flex-1  items-center'>
                        <p className='px-1 text-white hover:text-gray-100 font-light text-md '>Recommended : </p>
                        <p className='px-1 text-white hover:text-gray-100 font-bold text-lg '>{job.relevance_score}</p>
                    </div>
}
                    {job.experience && 
                    <div className='flex flex-col flex-1 items-center'>
                    <p className='text-white hover:text-gray-100 font-light text-md '>experience:</p>
                    <p className='text-white hover:text-gray-100 font-light text-md '>{job.experience}</p>
                    </div>
                    }
                </div>
            </label>
        ))}
        

        </div>
    </>
  )
}

export default JobCards