"use client"
import React, { useRef } from 'react'
import Image from "next/image";
import { motion, useInView } from "framer-motion";

const Features = () => {
    const ref = useRef(null)
    const isInView = useInView(ref, { once: true });
  return (
            <div className={'place-items-center'} id='features-section'>
                <div className='bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 features w-[98%] py-0 cursor-default'>
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
                        <div className='flex flex-col md:flex-row px-6 lg:px-32 py-10 gap-6 md:gap-10 justify-between shadow-black-500 shadow-lg'>
               
                                <div className='w-full h-48 md:size-64'>
                                    <img src={"/resume.jpg"} alt='tailor' className='w-full h-full object-cover rounded-lg'></img>
                </div>
                                <div className='flex-1 p-5 content-center text-center md:text-left'>
                                        <h1 className='text-2xl font-bold'>Craft Your Perfect Resume</h1>
                                        <p className='text-lg md:text-xl mt-3'>Build a polished, professional resume in minutes. HireHawk’s intuitive builder works for all industries—showcase your skills and experience, no matter your background.</p>
                </div>
            </div>
            </motion.div>

               <motion.h1
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                whileHover={{ scale: 1.01 }}
                >
            <div className='flex flex-col md:flex-row-reverse px-6  lg:px-32 py-10 gap-6 md:gap-10 justify-between shadow-black-500 shadow-lg overflow-hidden'>
                <div className='flex-1 p-5 content-center text-center md:text-right'>
                    <h1 className='text-2xl font-bold'>Skill-to-Job Matching</h1>
                    <p className='text-lg md:text-xl mt-3'>HireHawk's intelligent matching engine analyzes your unique abilities and pairs you with roles where you'll truly excel. We spotlight your strengths for every opportunity—so you get noticed for the talents that matter most</p>
                </div>
                 <div className='w-full h-48 md:size-64'>
                  <img src={"/1.png"} alt='scraper' className='w-full h-full object-cover rounded-lg'></img>
                </div>
            </div>
                </motion.h1>

           <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                whileHover={{ scale: 1.01 }}
                >
                        <div className='flex flex-col md:flex-row px-6 lg:px-32 py-10 gap-6 md:gap-10 justify-between shadow-black-500 shadow-lg'>
                                <div className='w-full h-48 md:size-64'>
                                    <img src={"/tailor.jpg"} alt='tailor' className='w-full h-full object-cover rounded-lg'></img>
                </div>
                                <div className='flex-1 content-center p-5 text-center md:text-left'>
                                        <h1 className='text-2xl font-bold'>Tailored Applications, Better Results</h1>
                                        <p className='text-lg md:text-xl mt-3'>Stop blending in with generic resumes. HireHawk analyzes every job listing and customizes your application to highlight your most relevant strengths, boosting your chances for any role. No more one-size-fits-all — every application gets a personal touch.</p>
                </div>
            </div>
            </motion.div>
            

            <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            whileHover={{ scale: 1.01 }}
            >
            <div className='flex flex-col md:flex-row-reverse px-6 lg:px-32 py-10 gap-6 md:gap-10 justify-between shadow-black-500 shadow-lg'>
                <div className='flex-1 p-5 content-center text-center md:text-right'>
                    <h1 className='text-2xl font-bold'>The Smart Applier</h1>
                    <p className='text-lg md:text-xl mt-3'>Automate your applications with precision. Smart Applier fills out forms, attaches tailored documents, and keeps track of your progress — so you can focus on preparing for interviews.</p>
                </div>
                <div className='w-full h-48 md:size-64'>
                    <img src={"/apply.png"} alt='applier' className='w-full h-full object-cover rounded-lg'></img>
                </div>
            </div>
            </motion.div>
        </motion.div>
        </div>
    </div>
  )
}

export default Features