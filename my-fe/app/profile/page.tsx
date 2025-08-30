import React from 'react'
import Image from "next/image";


const page = () => {
  return (
    <div className='h-screen overflow-hidden flex gap-10 items-center text-white mx-32 p-6'>
        <div className=' rounded-3xl flex justify-center shadow-[0px_0px_20px_5px_rgba(255,255,255,0.2)] p-6 '>
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

        <div className=' rounded-3xl shadow-[0px_0px_20px_5px_rgba(255,255,255,0.2)] p-6 px-10 flex flex-col  gap-3  text-white w-[70%] h-120'>
            <div className=' flex flex-col gap-0 w-full h-full  rounded-xl'>
                <div className=' h-16 flex gap-1 w-full'>
                    <div className=' flex-1 justify-between items-center flex flex-col'>
                        <p className='pt-5'>BIO</p>
                        <div className='w-full h-1 bg-blue-500'></div>
                    </div>
                    <div className=' flex-1 justify-between items-center flex flex-col'>
                        <p className='pt-5'>VERIFIED</p>
                        <div className='w-full h-1 bg-white'></div>
                    </div>
                </div>
                {/* <div className='w-full h-1 bg-blue-500'></div> */}
                <div className=' shadow-[0px_0px_20px_5px_rgba(0,0,0,0.2)] rounded-bl-xl rounded-br-xl flex flex-col justify-center gap-1  h-full px-30'>
                    <div className='inline-flex gap-8 items-center border px-10 justify-between'><h2 className='text-3xl font-bold'>User name:</h2><p className='text-xl font-light'>Srinivas sai saran teja</p></div>
                    <div className='inline-flex gap-8 items-center border px-10 justify-between'><h2 className='text-3xl'>email:</h2><p className='text-xl font-light'> teja@gmail.com</p></div>
                    <div className='inline-flex gap-8 items-center border px-10 justify-between'><h2 className='text-3xl'>phone:</h2><p className='text-xl font-light'> 7410852096</p></div>
                    <div className='inline-flex gap-8 items-center border px-10 justify-between'><h2 className='text-3xl'>Job applied:</h2><p className='text-xl font-light'> 50</p></div>
                </div>
            </div>
        </div>
    </div>
  )
}

export default page