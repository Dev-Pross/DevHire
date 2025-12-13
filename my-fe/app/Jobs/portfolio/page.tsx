import React from 'react'
import PortfolioPage from '../../Components/PortfolioPage'
import Navbar from '../../Components/Navbar'

const page = () => {
  return (
    <div className="page-section h-full">
      <Navbar />
        <PortfolioPage/>
    </div>
  )
}

export default page