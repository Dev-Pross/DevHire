"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import getLoginUser from "@/app/utiles/getUserData";

export const HeroTalent = () => {
  const [id, setId] = useState<string | null>(null);
  const [resume, setResume] = useState<string | null>(null);

  useEffect(() => {

    async function getUser() {
      const { data, error } = await getLoginUser();
      if(data?.user){
        setId(data.user.id)
      }
      
    }
    getUser()
  }, []);

  useEffect(()=>{
    async function getResume(){
      
      if(id){
        const res = sessionStorage.getItem("resume")
        console.log(res);
        
        setResume(res == null ? null : res)
      }
    }
    getResume()
    console.log(resume);
    
  },[id, resume])

  return (
    <section className="w-full h-screen relative">
      <div className="hidden lg:flex h-full w-full items-center lg:px-15 xl:px-30 mb-10">
        <div className="flex-1.5 w-[50%] z-10 absolute">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1
              className="xl:text-7xl lg:text-6xl  xl:font-bold lg:[-webkit-text-stroke:2px_white] xl:[-webkit-text-stroke:3px_white] text-transparent leading-tight mb-6">
              Unleash Your Potential. Land Your Job
            </h1>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <p className="xl:text-2xl lg:text-lg  font-extralight text-white leading-tight mb-6">
              Try Smart Applier Now
            </p>
          </motion.div>

          <div>
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              {id ? (
                <div className="flex space-x-2">
                  <Link href={"/Jobs/LinkedinUserDetails"}>
                    <button className="cursor-pointer bg-gradient-to-r from-[#FFFF00] to-[#FFD700] text-black xl:text-lg text-sm font-bold hover:bg-gradient-to-r hover:from-[#FF6B35] hover:to-[#F7931E] hover:text-white transition-all duration-300 hover:scale-110 hover:shadow-2xl px-6 py-4 xl:px-8 xl:py-4 rounded-lg">
                      Upload Resume
                    </button>
                  </Link>
                  {resume && (
                    <Link href={"/Jobs"}>
                      <button className="cursor-pointer hover:bg-gray-300 hover:text-[#8B5FBF] text-sm xl:text-lg font-bold transition-all duration-300 hover:scale-105 py-4 rounded-lg bg-gray-100 text-black px-6 xl:px-8">
                        Find your perfect Job
                      </button>
                    </Link>
                  )}
                </div>
              ) : (
                <div className="flex space-x-4">
                  <Link href="/login">
                    <button className="cursor-pointer bg-gradient-to-r from-[#FFFF00] to-[#FFD700] text-black xl:text-lg text-sm font-bold hover:bg-gradient-to-r hover:from-[#FF6B35] hover:to-[#F7931E] hover:text-white transition-all duration-300 hover:scale-110 hover:shadow-2xl px-8 py-4 rounded-lg">
                      Get Started
                    </button>
                  </Link>
                  <Link href="/register">
                    <button className="cursor-pointer hover:bg-gray-300 hover:text-[#8B5FBF] font-bold xl:text-lg text-sm transition-all duration-300 hover:scale-105 py-4 rounded-lg bg-gray-100 text-black px-8">
                      Upload Resume
                    </button>
                  </Link>
                </div>
              )}
            </motion.div>
          </div>
        </div>

        <div className="lg:w-[60%] xl:w-[45%] lg:ml-[40%] xl:ml-[50%] relative flex justify-center opacity-75">
          <div className="left-0 relative">
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <img
                src="/ne.jpg"
                alt="Product showcase"
                className="w-96 h-120 object-cover rounded-2xl shadow-2xl "
              />
              <div className="absolute -top-4 -right-4 w-24 h-24 bg-blue-500 rounded-full opacity-20"></div>
            </motion.div>
          </div>
        </div>
{/* Tailor resume part */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="w-full text-center ml-5">
            <h1
              className="text-5xl font-thin text-transparent leading-tight mb-6  xl:[-webkit-text-stroke:2px_white] lg:[-webkit-text-stroke:2px_black]">
              Need a Perfect Resume?
            </h1>
            <p className="xl:text-2xl lg:text-lg font-extralight xl:text-white lg:text-gray-700 leading-tight mb-6">
              Try our Resume Tailor for personalized results.
            </p>
            <Link href={"/Jobs/tailor"}>
              <button className="cursor-pointer border content-center bg-gradient-to-r from-[#10B981] to-[#059669] text-white font-bold xl:text-lg text-sm hover:from-[#059669] hover:to-[#047857] transition-all duration-300 hover:scale-105 px-8 py-4 rounded-lg">
                Checkout our Resume Tailor
              </button>
            </Link>
          </div>
        </motion.div>
      </div>

      {/* Mobile/Tablet: simplified responsive view without image */}
      <div className="flex lg:hidden min-h-[90vh] h-max w-full items-center justify-center px-4 py-8">
        <div className="w-full max-w-md bg-white/5 backdrop-blur-md rounded-2xl p-8 shadow-2xl">
          <div className="flex flex-col items-center justify-center text-center gap-6">
            <motion.h1
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="text-3xl sm:text-4xl font-bold text-white drop-shadow-lg"
              style={{ WebkitTextStroke: "1px white" }}
            >
              Unleash Your Potential. Land Your Job
            </motion.h1>
            
            <motion.p
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-lg sm:text-xl text-white/90"
            >
              Try Smart Applier Now
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="w-full flex flex-col gap-4"
            >
              {id ? (
                <>
                  <Link href={"/Jobs/LinkedinUserDetails"}>
                    <button className="w-full bg-gradient-to-r from-[#FFFF00] to-[#FFD700] text-black font-bold hover:from-[#FF6B35] hover:to-[#F7931E] hover:text-white transition-all duration-300 hover:scale-105 px-6 py-4 rounded-lg">
                      Upload Resume
                    </button>
                  </Link>
                  {(resume) && (
                    <Link href={"/Jobs"}>
                      <button className="w-full bg-gray-100 hover:bg-gray-300 text-black font-bold transition-all duration-300 hover:scale-105 px-6 py-4 rounded-lg">
                        Find your perfect Job
                      </button>
                    </Link>
                  )}
                </>
              ) : (
                <>
                  <Link href="/login">
                    <button className="w-full bg-gradient-to-r from-[#FFFF00] to-[#FFD700] text-black font-bold hover:from-[#FF6B35] hover:to-[#F7931E] hover:text-white transition-all duration-300 hover:scale-105 px-6 py-4 rounded-lg">
                      Get Started
                    </button>
                  </Link>
                  <Link href="/register">
                    <button className="w-full bg-gray-100 hover:bg-gray-300 text-black font-bold transition-all duration-300 hover:scale-105 px-6 py-4 rounded-lg">
                      Upload Resume
                    </button>
                  </Link>
                </>
              )}
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="border-t border-white/20 pt-6 mt-4 w-full"
            >
              <h3 className="text-xl sm:text-2xl font-bold text-white mb-3">Need a Perfect Resume?</h3>
              <p className="text-white/80 text-sm sm:text-base mb-4">Try our Resume Tailor for personalized results.</p>
              <Link href={"/Jobs/tailor"}>
                <button className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-6 py-3 rounded-lg shadow-lg transition-all">
                  Checkout our Resume Tailor
                </button>
              </Link>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
};
