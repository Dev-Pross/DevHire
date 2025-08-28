import React from 'react'
import Image from "next/image";


const page = () => {
  return (
    <div className='h-screen overflow-hidden flex gap-10 items-center text-white mx-32 p-6'>
        <div className='border rounded-3xl flex justify-center shadow-[0px_0px_20px_5px_rgba(255,255,255,0.2)] p-6 '>
        <div className=' rounded flex flex-col gap-3 items-center overflow-hidden  p-6 px-8'>
            <div className=' inset-ring-4 inset-ring-[#4b4d51] inset-shadow-sm rounded-full overflow-hidden'>
            <Image 
                src={"/profile.svg"}
                alt="Profile Icon"
                width={310}
                height={50}
            ></Image>
            </div>

            <div className='border w-full gap-2 flex flex-col' >
                <button className='border'>Edit</button>
                <button className='border'>logout</button>
            </div>
        </div>
        </div>
        <div className='border rounded-3xl shadow-[0px_0px_20px_5px_rgba(255,255,255,0.2)] p-6 px-30 flex flex-col justify-center gap-3 items-start text-white w-[70%] h-120'>
            <div className='inline-flex gap-8 items-center'><h2 className='text-3xl font-bold'>User name:</h2><p className='text-xl font-light'> teja</p></div>
            <div className='inline-flex gap-8 items-center'><h2 className='text-3xl'>email:</h2><p className='text-xl font-light'> teja@gmail.com</p></div>
            <div className='inline-flex gap-8 items-center'><h2 className='text-3xl'>phone:</h2><p className='text-xl font-light'> 7410852096</p></div>
            <div className='inline-flex gap-8 items-center'><h2 className='text-3xl'>Job applied:</h2><p className='text-xl font-light'> 50</p></div>
        </div>
    </div>
  )
}

export default page