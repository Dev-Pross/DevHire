import React from 'react'

const Navbar = () => {
  return (
    <div className='max-w-7xl mx-auto m-0 sticky top-0 z-50'>
        <nav className='flex justify-between items-center text-white gap-4 p-4'>
            <div className=''>logo</div>
            <div className='flex gap-4'>
                <a className='text-white hover:text-gray-300 font-bold' href='#'>Home</a>
                <a className='text-white hover:text-gray-300 font-bold' href='#'>Pricing</a>
                <a className='text-white hover:text-gray-300 font-bold' href='#'>About us</a>
            </div>
            <a className='rounded-4xl pl-4 pr-4 border-2 p-1' href='#'>
                Get Started
            </a>
        </nav>
    </div>
  )
}

export default Navbar