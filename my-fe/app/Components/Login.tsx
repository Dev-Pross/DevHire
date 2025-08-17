"use client"
import React, { useState } from 'react'
import { supabase } from '../supabaseClient'
import { useRouter } from 'next/navigation'

const Login = () => {

    const[email, setEmail] = useState("")
    const[password, setPassword] = useState("")
    const[error, setError] = useState<any | null>(null)
    const router = useRouter()


    const LoginHandle = async()=>{
        // console.log(`user: ${email} password: ${password}`);
        setError(null)
        try {

            if(!email || !password){
                setError("Email and password are required");
            }
              const { error: supabaseError } = await supabase.auth.signInWithPassword({
              email: email,
              password: password,
              
            });
        
            if (supabaseError) {
              console.log("Supabase sign-in failed:", supabaseError.message);
            }
            else{
                console.log("Login successful");
                router.push("/");
            }
        } catch (err: any) {
            if (err && err.response && err.response.status === 401) {
            console.log("Invalid email or password.");
            } else {
            console.log("An error occurred during signin.");
            }
            console.log(err);
        }
    }
    
  return (
    <>
        <div className='' >
            <div className='p-4 showdow-sm max-w-xs mx-auto mt-10 '>
                <h2 className='text-2xl font-bold text-center text-white mb-6'>Login</h2>
                {error && <div className='w-full text-center mb-2 text-red-500'>{error}!!</div>}

                <form>
                    <div className='mb-4'>
                        <input className='shadow appearance-none border rounded w-full bg-[#325b4b] py-2 px-3 text-white leading-tight border-none focus:outline-none focus:shadow-outline' id='username' type='text' placeholder='Email' onChange={(e)=>setEmail(e.target.value)}/>
                    </div>
                    <div className='mb-6'>
                        <input className='shadow appearance-none border rounded w-full py-2 px-3 bg-[#325b4b] text-white mb-3 leading-tight border-none focus:outline-none focus:shadow-outline' id='password' type='password' placeholder='Password' onChange={(e)=>setPassword(e.target.value)}/>
                    </div>
                    <div className='flex items-center justify-between px-10'>
                        <button onClick={LoginHandle} className='bg-[#27db78] hover:bg-[#159950] w-full text-black font-bold py-2 px-4 rounded-4xl focus:outline-none focus:shadow-outline' type='button'>
                            Sign In
                        </button>
                    </div>
                </form>
                <div className='w-full text-center mt-4 text-white'>
                    Dont have an account? <a href='#' className='text-blue-500'>Register</a>
                </div>
            </div>
        </div>
    </>
  )
}

export default Login