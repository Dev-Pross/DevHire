"use client";
import { useEffect } from "react";
import { supabase } from "../../utiles/supabaseClient";
import { useState } from "react";
import getLoginUser from "@/app/utiles/getUserData";
import Link from "next/link";
import { motion } from "framer-motion";
export const HeroTalent = () => {
  const [id, setId] = useState<string | null>(null);
  const [resume, setResume] = useState<string | null>(null);
  // const router = useRouter();
  useEffect(() => {
    // const id = sessionStorage.getItem("id")
    const resume_url = sessionStorage.getItem("resume");
    // setId(id)
    // if(!id) return
    async function getResume() {
      const { data, error } = await getLoginUser();
      console.log("session ", data);
      if (error) {
        console.error("Error fetching user:", error);
      } else if (data?.user) {
        console.log(
          "User is logged in:",
          data?.user.user_metadata.email,
          " ",
          data?.user.user_metadata.username
        );
      } else {
        console.log("No user is logged in.");
      }
      // setUser(data.user.user_metadata);
      sessionStorage.setItem("id", data?.user.user_metadata.sub);
      setId(data?.user.user_metadata.sub);
      sessionStorage.setItem("name", data?.user.user_metadata.username);
      sessionStorage.setItem("email", data?.user.user_metadata.email);

      if (id) {
        const res = await fetch(`/api/User?id=${id}`, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        });
        const resume_data = await res.json();
        console.log("mydata", resume_data.user.resume_url);
        if (!resume_url)
          sessionStorage.setItem("resume", resume_data.user.resume_url);
        setResume(resume_data.user.resume_url);
      }
    }
    getResume();
  }, [id]);
  return (
    <section className="h-screen w-full flex items-center px-30  ">
      <div className="flex-1.5 w-[50%] z-10 absolute">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-6xl font-bold bg-gradient-to-r from-white to-white/50 bg-clip-text text-transparent leading-tight mb-6">
            Unleash Your Potential. <br />
            Land Your Perfect Job  <br />with HireHawk. <br />
            Automate Job <br /> Applications <br />
          </h1>
        </motion.div>

        {/* <p className="text-xl text-stone-200 mb-8 leading-relaxed"> */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          {/* <p className="text-2xl font-extralight text-white/80 leading-tight mb-6">
            Harness the power of intelligent matching and effortless resume
            tailoring with HireHawk. Our platform connects your unique skills to
            the right opportunities.Automate
            applications, personalize your approach, and discover jobs that
            truly fit you. Your journey to a better career starts here.
          </p> */}
          <p className="text-2xl font-extralight text-white leading-tight mb-6">
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
              <div className="flex space-x-4">
                <Link href={"/LinkedinUserDetails"}>
                  <button className=" cursor-pointer border  bg-transparent  border-border-green-700 hover:bg-blue-600  text-white px-8 py-4 rounded-lg transition-colors">
                    Upload Resume
                  </button>
                </Link>
                {resume && (
                  <Link href={"/Jobs"}>
                    <button className="cursor-pointer border hover:bg-blue-600 hover:border-gray-300 text-white-700  py-4 rounded-lg bg-gray-100 text-black transition-colors px-8">
                      Proceed
                    </button>
                  </Link>
                )}
              </div>
            ) : (
              <div className="flex space-x-4">
                <Link href="/login">
                  <button className="cursor-pointer border hover:bg-blue-600 hover:border-gray-300 text-white-700  py-4 rounded-lg bg-gray-100 text-black transition-colors px-8">
                    Get Started
                  </button>
                </Link>
                <button className=" cursor-pointer border  bg-transparent  border-border-green-700 hover:bg-blue-600  text-white px-8 py-4 rounded-lg transition-colors">
                  Upload resume
                </button>
              </div>
            )}
          </motion.div>
        </div>

        {/* <div className="space-x-4">
       
       
        </div> */}
      </div>

      <div className="w-[30%] ml-[45%] relative flex justify-center opacity-75">
        <div className="left-0 relative">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <img
              src="/ne.jpg"
              alt="Product showcase"
              className="w-96 h-150 object-cover rounded-2xl shadow-2xl "
            />
            <div className="absolute -top-4 -right-4 w-24 h-24 bg-blue-500 rounded-full opacity-20"></div>
          </motion.div>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className=" w-full text-center">
          <h1 className="text-4xl font-bold text-white leading-tight mb-6">
            Need a Custom Resume?
          </h1>
          <p className="text-2xl font-extralight text-white/80 leading-tight mb-6">
            Try our Resume Tailor for personalized results.
          </p>
          <Link href={"/LinkedinUserDetails"}>
            <button className=" cursor-pointer border content-center bg-white  border-border-green-700 hover:bg-blue-400  text-bg-clip px-8 py-4 rounded-lg transition-colors">
              Checkout our Resume Tailor
            </button>
          </Link>
        </div>
      </motion.div>
    </section>
  );
};
