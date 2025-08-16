import React from 'react'

const Navbar = () => {
  return (
    <div className='max-w-7xl mx-auto m-0'>
        <nav className='flex justify-between items-center text-white gap-4 p-4'>
            <div className=''>logo</div>
            <div className='flex gap-4'>
                <a className='text-white hover:text-gray-300 ' href='#'><strong>Home</strong></a>
                <a className='text-white hover:text-gray-300 font-bold' href='#'>Pricing</a>
                <a className='text-white hover:text-gray-300 font-bold' href='#'>About us</a>
            </div>
            <div className=''>get started</div>
        </nav>
    </div>
  )
}

export default Navbar