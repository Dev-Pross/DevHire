import React from 'react'
import Navbar from '../Components/Navbar'
import { Pricing } from '../Components/Pricing/Pricing'

const page = () => {
  return (
    <div className='page-section'>
      <Navbar/>
      <Pricing/>
    </div>
  )
}

export default page