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

const JobCards: React.FC<JobCardsProps> = ({ jobs = []}) => {


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
        <div className='w-full   p-4 flex justify-between items-center sticky top-15 backdrop-blur-xl z-50 '>
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
                className={`m-5 ml-8 mr-8 ml-4 rounded-xl h-100 cursor-pointer min-w-sm max-w-sm bg-[#052718] shadow-lg shadow-[#052718]-500 relative 
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