"use client"
import React, { useRef } from 'react'
import Image from "next/image";
import { motion, useInView } from "framer-motion";

const Features = () => {
    const ref = useRef(null)
    const isInView = useInView(ref, { once: true });
  return (
      <div className='w-full flex justify-center py-8 lg:py-12' id='features-section'>
        <div className='bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 features w-full max-w-7xl mx-4 rounded-xl cursor-default'>
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 50 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 1, ease: "easeOut" }}
          className="space-y-8 lg:space-y-12"
        >
            {/* Feature 1 */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                whileHover={{ scale: 1.01 }}
            >
            <div className='flex flex-col md:flex-row px-6 sm:px-12 lg:px-20 py-8 lg:py-10 gap-6 lg:gap-10 items-center shadow-lg'>
                <div className='w-full md:w-48 lg:w-64 h-48 lg:h-64 flex-shrink-0'>
                  <img src={"/resume.jpg"} alt='tailor' className='w-full h-full object-cover rounded-lg shadow-xl'></img>
                </div>
                <div className='flex-1 p-4 lg:p-5 text-center md:text-left'>
                    <h1 className='text-xl lg:text-2xl xl:text-3xl font-bold mb-3'>Craft Your Perfect Resume</h1>
                    <p className='text-base lg:text-lg xl:text-xl leading-relaxed'>Build a polished, professional resume in minutes. HireHawk's intuitive builder works for all industries—showcase your skills and experience, no matter your background.</p>
                </div>
            </div>
            </motion.div>

            {/* Feature 2 */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                whileHover={{ scale: 1.01 }}
            >
            <div className='flex flex-col md:flex-row-reverse px-6 sm:px-12 lg:px-20 py-8 lg:py-10 gap-6 lg:gap-10 items-center shadow-lg'>
                <div className='w-full md:w-48 lg:w-64 h-48 lg:h-64 flex-shrink-0'>
                  <img src={"/1.png"} alt='scraper' className='w-full h-full object-cover rounded-lg shadow-xl'></img>
                </div>
                <div className='flex-1 p-4 lg:p-5 text-center md:text-right'>
                    <h1 className='text-xl lg:text-2xl xl:text-3xl font-bold mb-3'>Skill-to-Job Matching</h1>
                    <p className='text-base lg:text-lg xl:text-xl leading-relaxed'>HireHawk's intelligent matching engine analyzes your unique abilities and pairs you with roles where you'll truly excel. We spotlight your strengths for every opportunity—so you get noticed for the talents that matter most</p>
                </div>
            </div>
            </motion.div>

            {/* Feature 3 */}
           <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                whileHover={{ scale: 1.01 }}
            >
            <div className='flex flex-col md:flex-row px-6 sm:px-12 lg:px-20 py-8 lg:py-10 gap-6 lg:gap-10 items-center shadow-lg'>
                <div className='w-full md:w-48 lg:w-64 h-48 lg:h-64 flex-shrink-0'>
                  <img src={"/tailor.jpg"} alt='tailor' className='w-full h-full object-cover rounded-lg shadow-xl'></img>
                </div>
                <div className='flex-1 p-4 lg:p-5 text-center md:text-left'>
                    <h1 className='text-xl lg:text-2xl xl:text-3xl font-bold mb-3'>Tailored Applications, Better Results</h1>
                    <p className='text-base lg:text-lg xl:text-xl leading-relaxed'>Stop blending in with generic resumes. HireHawk analyzes every job listing and customizes your application to highlight your most relevant strengths, boosting your chances for any role. No more one-size-fits-all — every application gets a personal touch.</p>
                </div>
            </div>
            </motion.div>

            {/* Feature 4 */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                whileHover={{ scale: 1.01 }}
            >
            <div className='flex flex-col md:flex-row-reverse px-6 sm:px-12 lg:px-20 py-8 lg:py-10 gap-6 lg:gap-10 items-center shadow-lg'>
                <div className='w-full md:w-48 lg:w-64 h-48 lg:h-64 flex-shrink-0'>
                    <img src={"/apply.png"} alt='applier' className='w-full h-full object-cover rounded-lg shadow-xl'></img>
                </div>
                <div className='flex-1 p-4 lg:p-5 text-center md:text-right'>
                    <h1 className='text-xl lg:text-2xl xl:text-3xl font-bold mb-3'>The Smart Applier</h1>
                    <p className='text-base lg:text-lg xl:text-xl leading-relaxed'>Automate your applications with precision. Smart Applier fills out forms, attaches tailored documents, and keeps track of your progress — so you can focus on preparing for interviews.</p>
                </div>
            </div>
            </motion.div>
        </motion.div>
        </div>
    </div>
  )
}

export default Features
