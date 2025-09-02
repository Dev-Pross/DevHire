"use client"
import React, { useRef } from 'react'
import Image from "next/image";
import { motion, useInView } from "framer-motion";

const Features = () => {
    const ref = useRef(null)
    const isInView = useInView(ref, { once: true });
  return (
      <div className={'place-items-center'}>
        <div className='bg-white w-[98%] py-0  cursor-default'>
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 50 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}} // animate only when in view
          transition={{ duration: 1, ease: "easeOut" }}
        >
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                whileHover={{ scale: 1.0125 }}
                >
            <div className=' flex px-32 py-10 gap-10 justify-between shadow-black-500 shadow-lg'>
               
                <div className='size-64'>
                  <img src={"/resume.jpg"} alt='tailor' className='w-full rounded-lg h-full'></img>
                </div>
                <div className='flex-5  p-5 content-center'>
                    <h1 className=' text-2xl font-bold '>Craft Your Perfect Resume</h1>
                    <p className=' text-xl mt-3'>Build a polished, professional resume in minutes. HireHawk’s intuitive builder works for all industries—showcase your skills and experience, no matter your background.</p>
                </div>
            </div>
            </motion.div>

               <motion.h1
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                whileHover={{ scale: 1.01 }}
                >
            <div className=' flex px-32 py-10 gap-10 justify-between shadow-black-500 shadow-lg oberflow-hidden'>
                <div className='flex-10  p-5 content-center'>
                    <h1 className='text-end text-2xl font-bold '>Skill-to-Job Matching</h1>
                    <p className='text-end text-xl mt-3'>HireHawk's intelligent matching engine analyzes your unique abilities and pairs you with roles where you'll truly excel. We spotlight your strengths for every opportunity—so you get noticed for the talents that matter most</p>
                </div>
                 <div className='size-64'>
                  <img src={"/1.png"} alt='scraper' className='w-full rounded-lg h-full'></img>
                </div>
            </div>
                </motion.h1>

           <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                whileHover={{ scale: 1.01 }}
                >
            <div className=' flex px-32  py-10 gap-10 justify-between shadow-black-500 shadow-lg'>
                <div className='size-64'>
                  <img src={"/tailor.jpg"} alt='tailor' className='w-full rounded-lg h-full'></img>
                </div>
                <div className='flex-10  content-center p-5'>
                    <h1 className='text-start text-2xl font-bold'>Tailored Applications, Better Results</h1>
                    <p className='text-start text-xl mt-3'>Stop blending in with generic resumes. HireHawk analyzes every job listing and customizes your application to highlight your most relevant strengths, boosting your chances for any role. No more one-size-fits-all — every application gets a personal touch.</p>
                </div>
            </div>
            </motion.div>
            

            <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            whileHover={{ scale: 1.01 }}
            >
            <div className=' flex px-32 p-10 gap-10 justify-between shadow-black-500 shadow-lg'>
                <div className='flex-10  p-5 content-center'>
                    <h1 className='text-end text-2xl font-bold '>The Smart Applier</h1>
                    <p className='text-end text-xl mt-3'>Automate your applications with precision. Smart Applier fills out forms, attaches tailored documents, and keeps track of your progress — so you can focus on preparing for interviews.</p>
                </div>
                <div className='size-64 w-74'>
                    <img src={"/apply.png"} alt='applier' className='w-full rounded-lg h-full'></img>
                </div>
            </div>
            </motion.div>
        </motion.div>
        </div>
    </div>
  )
}

export default Features