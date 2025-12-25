'use client'
import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { supabase } from '../utiles/supabaseClient';
import toast from 'react-hot-toast';

export default function ResetPasswordPage() {
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false)
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

//   const searchParams = useSearchParams();

//   useEffect(() => {
//     const code = searchParams.get("code")
//     //supabse will automatically handles this code
//   }, []);

  const handleReset = async () => {

    if(confirmPassword != password){
        toast.error('passwords not matched')
        setMessage('passwords not matched')
        return
    }
    const { data, error } = await supabase.auth.updateUser({ password });
    if (error) {
      setMessage(error.message);
      if(error.message.includes("least 6 characters")) toast.error("Password should be stronger")
      else toast.error(error.message)
    } else {
      toast.success("Password updated! You can now log in.")
      setMessage('Password updated! You can now log in.');
      router.push('/login');
    }
  };

  return (
    <div className="min-h-screen page-section flex items-center justify-center px-4 sm:px-6">
      <div className="w-full max-w-md">
        <div className="bg-white/5 backdrop-blur-lg p-6 sm:p-8 lg:p-10 rounded-2xl shadow-2xl border border-white/10">
          <h2 className="text-2xl sm:text-3xl font-bold text-center inline-flex text-white mb-6 lg:mb-8">
            Reset Password
          </h2>
          {message && (
            <div className="w-full text-center mb-4 p-3 bg-red-500/20 border border-red-500 rounded-lg text-red-200 text-sm">
              {message}
            </div>
          )}

          <form className="space-y-4">
            <div>
                <div className="relative">
                    <input className='shadow appearance-none border border-white/20 rounded-lg w-full py-3 px-4 pr-12 bg-[#325b4b]/80 text-white leading-tight focus:outline-none focus:ring-2 focus:ring-green-500 transition-all' id='password' type={showPassword ? "text" : "password"} placeholder='Password' onChange={(e)=>setPassword(e.target.value)} required/>
                    <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors focus:outline-none"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                        {showPassword ? (
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                            </svg>
                        ) : (
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                        )}
                    </button>
                </div>
            </div>
            <div>
                <div className="relative">
                    <input className='shadow appearance-none border border-white/20 rounded-lg w-full py-3 px-4 pr-12 bg-[#325b4b]/80 text-white leading-tight focus:outline-none focus:ring-2 focus:ring-green-500 transition-all' id='confirmPassword' type={showConfirmPassword ? "text" : "password"} placeholder='Confirm Password' onChange={(e)=>setConfirmPassword(e.target.value)} required/>
                    <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors focus:outline-none"
                        aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                    >
                        {showConfirmPassword ? (
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                            </svg>
                        ) : (
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                        )}
                    </button>
                </div>
            </div>
            <div>
            </div>
            <div className="pt-2">
              <button
                onClick={handleReset}
                disabled={loading}
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
                  <span>Reset</span>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}