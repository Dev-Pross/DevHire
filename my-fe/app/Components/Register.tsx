"use client"
import React, { useState } from 'react'
import { supabase } from '../utiles/supabaseClient'
import {useRouter} from 'next/navigation'

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
            setLoading(false)
        }
        else if(password !== confirmPassword){
            setError("password not match");
            setLoading(false)
        }
        else if(! isStrongPassword(password)){
            setError("password isn't strong enough");
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
            emailRedirectTo: 'http://localhost:3000/login',
            },
        })
        if(error){
            console.log("error",error);
            setLoading(false)
            setError("failed to establish connection with server")
        }
        else{
            console.log("success", data); 
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
    <div className=''>
        <div className='p-4 showdow-sm max-w-xs mx-auto mt-10 '>
            <h2 className='text-2xl font-bold text-center text-white mb-6'>Register</h2>
            {error && <div className='w-full text-center mb-2 text-red-500'>{error}!!</div>}
                <form>
                    <div className='mb-4'>
                        <input className='shadow appearance-none border rounded w-full bg-[#325b4b] py-2 px-3 text-white leading-tight border-none focus:outline-none focus:shadow-outline' id='username' type='text' placeholder='Username' onChange={(e)=>setUsername(e.target.value)} required/>
                    </div>
                    <div className='mb-4'>
                        <input className='shadow appearance-none border rounded w-full bg-[#325b4b] py-2 px-3 text-white leading-tight border-none focus:outline-none focus:shadow-outline' id='username' type='text' placeholder='Email' onChange={(e)=>setEmail(e.target.value)} required/>
                    </div>
                    <div className='mb-4'>
                        <input className='shadow appearance-none border rounded w-full py-2 px-3 bg-[#325b4b] text-white leading-tight border-none focus:outline-none focus:shadow-outline' id='password' type='password' placeholder='Password' onChange={(e)=>setPassword(e.target.value)} required/>
                    </div>
                    <div className='mb-6'>
                        <input className='shadow appearance-none border rounded w-full py-2 px-3 bg-[#325b4b] text-white mb-3 leading-tight border-none focus:outline-none focus:shadow-outline' id='password' type='password' placeholder='Confirm Password' onChange={(e)=>setConfirmPassword(e.target.value)} required/>
                    </div>
                    <div className='flex items-center justify-between px-10'>
                        <button onClick={RegisterHandler} className='bg-[#27db78] hover:bg-[#159950] w-full text-black font-bold py-2 px-4 rounded-4xl focus:outline-none focus:shadow-outline' type='button'>
                           {loading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <svg className="animate-spin h-5 w-5 text-black" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="black"/>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
                                    </svg>
                                    Signing up...
                                </span>
                                ) : (
                                <span className="bg-black bg-clip-text text-transparent">
                                    Sign Up
                                </span>
                                )}
                        </button>
                    </div>
                </form>
                <div className='w-full text-center mt-4 text-white'>
                    Already have an account? <a href='/login' className='text-blue-500'>Login</a>
                </div>
            </div>
    </div>
  )
}

export default Register