import React, { useEffect, useState } from 'react'
import { supabase } from '../utiles/supabaseClient'
import { useRouter } from 'next/navigation'

interface RestProps{
    onBack: ()=> void
}

const ResetPass = ({onBack}:RestProps) => {
    const [email, setEmail] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [loading, setLoading] = useState(false)
    const resendMailTime = 60000
    const [buttonShow, setButtonShow] = useState(false)
    const [resetTimer, setResetTimer] = useState(0)
    
    useEffect(()=>{
      if(buttonShow && resetTimer>0){
        const timer = setInterval(()=>{
          setResetTimer((prev)=>prev-1)
          console.log(`timer: ${resetTimer}`)
        },1000)
        return ()=> clearInterval(timer)
      }
    })

    const frontendURL = process.env.NEXT_PUBLIC_FRONT_URL as string || 'http://localhost:3000'
    const resetPassword = async()=>{
      
        setLoading(true)
        try{
            if(email){
                setError('Password reset link sent to your mail')
                const {data, error} = await supabase.auth.resetPasswordForEmail(email,{
                    redirectTo: `https://dev-hire-znlr.vercel.app/reset-password`
                })
                console.log(data)
                console.log(error)
                if(error?.message) setError(error?.message)
                setLoading(false)
            }
        }catch(e){
          setLoading(false)
          setError(e instanceof Error ? e.message : "Unknown Error")
        }
        setButtonShow(true)
        setResetTimer(60)
        setTimeout(() => {
          setButtonShow(false)
        }, resendMailTime);
  }
  return (
    <>
    <div className="min-h-screen flex items-center justify-center px-4 sm:px-6">
      <div className="w-full max-w-md">
        <div className="bg-white/5 backdrop-blur-lg p-6 sm:p-8 lg:p-10 rounded-2xl shadow-2xl border border-white/10">
          <h2 className="text-2xl sm:text-3xl font-bold text-center inline-flex text-white mb-6 lg:mb-8">
          <button className='text-xl font-light relative px-5 cursor-pointer bg-white/5 rounded-full place-self-center mr-2' 
            onClick={onBack}>&larr;</button>
            Reset Password
          </h2>
          {error && (
            <div className="w-full text-center mb-4 p-3 bg-red-500/20 border border-red-500 rounded-lg text-red-200 text-sm">
              {error}
            </div>
          )}

          <form className="space-y-4">
            <div>
              <input
                className="shadow appearance-none border border-white/20 rounded-lg w-full bg-[#325b4b]/80 py-3 px-4 text-white leading-tight focus:outline-none focus:ring-2 focus:ring-green-500 transition-all"
                id="username"
                type="email"
                placeholder="Email"
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
            </div>
            <div className="pt-2">
              <button
                onClick={resetPassword}
                disabled={loading || buttonShow}
                className="bg-[#27db78] hover:bg-[#159950] w-full text-black font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                type="button"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg
                      className="animate-spin h-5 w-5 text-black"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="black"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                      />
                    </svg>
                    Sending reset link...
                  </span>
                ) : (
                  buttonShow && resetTimer>0 ? (<span>Resend in {resetTimer}s</span>) :
                  (<span>Reset</span>)
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
    </>
)
}

export default ResetPass