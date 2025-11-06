"use client"
import React, { useState } from 'react'
import { supabase } from '../utiles/supabaseClient'
import {useRouter} from 'next/navigation'
import toast from 'react-hot-toast'

const Register = () => {

    const [email, setEmail] = React.useState("")
    const [password, setPassword] = React.useState("")
    const [confirmPassword, setConfirmPassword] = React.useState("")
    const [username, setUsername] = React.useState("")
    const [error, setError] = React.useState<string | null>(null)
    const [loading, setLoading] = useState(false)
    
    const router = useRouter()

    const RegisterHandler = ()=>{
        setError(null)
        
        if(!email || !password || !confirmPassword || !username){
            setError("All fields are required")
            toast.error("All fields are required")
            setLoading(false)
        }
        else if(password !== confirmPassword){
            setError("Password not match");
            toast.error("Password not match")
            setLoading(false)
        }
        else if(! isStrongPassword(password)){
            setError("Password should contain atleast 8 characters, one uppercase, 1 lowercase, 1 digit, 1 special character");
            toast.error("Password isn't strong enough")
            setLoading(false)
        }
        else{
            setLoading(true)
            signUpNewUser(email,password,username)
        }
    }

    async function signUpNewUser(email: string, password: string, username:string) {
        const { data, error } = await supabase.auth.signUp({
            email: email,
            password: password,
            options: {
                data:{
                    username: username
                },
            emailRedirectTo: 'https://dev-hire-znlr.vercel.app//login',
            },
        })
        if(error){
            // console.log("error",error);
            toast.error(`Failed to establish connection with server`)
            setLoading(false)
            setError("Failed to establish connection with server")
        }
        else{
            // console.log("success", data); 
            toast.success("Registration done successfully, please login.")
            fetch('api/User?action=insert',{
                method: "POST",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({
                    id:data.user?.user_metadata.sub,
                    name: username,
                    email:email
                })
            })
            router.push("/login")
        }
    }

    function isStrongPassword(password: string): boolean {
        // At least 8 characters, one uppercase, one lowercase, one digit, one special character
        return /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$/.test(password);
    }

  return (
    <div className='min-h-screen flex items-center justify-center px-4 sm:px-6'>
        <div className='w-full max-w-md'>
            <div className='bg-white/5 backdrop-blur-lg p-6 sm:p-8 lg:p-10 rounded-2xl shadow-2xl border border-white/10'>
            <h2 className='text-2xl sm:text-3xl font-bold text-center text-white mb-6 lg:mb-8'>Register</h2>
            {error && <div className='w-full text-center mb-4 p-3 bg-red-500/20 border border-red-500 rounded-lg text-red-200 text-sm'>{error}</div>}
                <form className='space-y-4'>
                    <div>
                        <input className='shadow appearance-none border border-white/20 rounded-lg w-full bg-[#325b4b]/80 py-3 px-4 text-white leading-tight focus:outline-none focus:ring-2 focus:ring-green-500 transition-all' id='username' type='text' placeholder='Username' onChange={(e)=>setUsername(e.target.value)} required/>
                    </div>
                    <div>
                        <input className='shadow appearance-none border border-white/20 rounded-lg w-full bg-[#325b4b]/80 py-3 px-4 text-white leading-tight focus:outline-none focus:ring-2 focus:ring-green-500 transition-all' id='email' type='text' placeholder='Email' onChange={(e)=>setEmail(e.target.value)} required/>
                    </div>
                    <div>
                        <input className='shadow appearance-none border border-white/20 rounded-lg w-full py-3 px-4 bg-[#325b4b]/80 text-white leading-tight focus:outline-none focus:ring-2 focus:ring-green-500 transition-all' id='password' type='password' placeholder='Password' onChange={(e)=>setPassword(e.target.value)} required/>
                    </div>
                    <div>
                        <input className='shadow appearance-none border border-white/20 rounded-lg w-full py-3 px-4 bg-[#325b4b]/80 text-white leading-tight focus:outline-none focus:ring-2 focus:ring-green-500 transition-all' id='confirmPassword' type='password' placeholder='Confirm Password' onChange={(e)=>setConfirmPassword(e.target.value)} required/>
                    </div>
                    <div className='pt-2'>
                        <button onClick={RegisterHandler} className='bg-[#27db78] hover:bg-[#159950] w-full text-black font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline transition-all disabled:opacity-50 disabled:cursor-not-allowed' type='button' disabled={loading}>
                           {loading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <svg className="animate-spin h-5 w-5 text-black" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="black"/>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
                                    </svg>
                                    Signing up...
                                </span>
                                ) : (
                                <span>
                                    Sign Up
                                </span>
                                )}
                        </button>
                    </div>
                </form>
                <div className='w-full text-center mt-6 text-white text-sm sm:text-base'>
                    Already have an account? <a href='/login' className='text-green-400 hover:text-green-300 font-semibold underline'>Login</a>
                </div>
            </div>
        </div>
    </div>
  )
}

export default Register