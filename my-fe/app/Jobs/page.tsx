"use client"
import React from 'react'
import Navbar from '../Components/Navbar'
import dynamic from 'next/dynamic'
const Jobs = dynamic(
  () => import('../Components/Jobs'),
  { ssr: false }
);
const page = () => {
  return (
    <div className='page-section'>
    <Navbar/>
    <Jobs/>
    </div>
  )
}

export default page
