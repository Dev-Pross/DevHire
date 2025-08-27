import { useEffect } from "react";
import { supabase } from "../../utiles/supabaseClient";
import { useState } from "react";
import getLoginUser from "@/app/utiles/getUserData";
import Link from "next/link";
import { motion } from "framer-motion";
import { useRouter } from "next/router";
export const HeroTalent = () => {
  const [user, setUser] = useState<{ email: string; user: string } | null>(
    null
  );
  // const router = useRouter();
  useEffect(() => {
    async function fetchSession() {
      const { data, error } = await supabase.auth.getSession();
      console.log("session ", data);
      if (error) {
        console.error("Error fetching user:", error);
      } else if (data.session?.user) {
        console.log(
          "User is logged in:",
          data.session?.user.user_metadata.email,
          " ",
          data.session?.user.user_metadata.username
        );
        setUser({
          email: data.session?.user.user_metadata.email,

          user: data.session?.user.user_metadata.username,
        });
      } else {
        console.log("No user is logged in.");
        setUser(null);
      }
    }
    fetchSession();
  }, []);
  return (
    <section className="h-screen w-full flex items-center px-30  ">
      <div className="flex-1 max-w-xl">
        <h1 className="text-6xl font-bold text-white  leading-tight mb-6">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            Build Amazing Products withsome amazing Developers <br />
          </motion.div>
        </h1>

        {/* <p className="text-xl text-stone-200 mb-8 leading-relaxed"> */}
        <div>
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            {user ? (
              <Link href={"/LinkedinUserDetails"}>
                <button className=" cursor-pointer border  bg-transparent  border-border-green-700 hover:bg-blue-600  text-white px-8 py-4 rounded-lg transition-colors">
                  Upload Resume
                </button>
              </Link>
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

      <div className="flex-1 flex justify-end opacity-80">
        <div className="relative">
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
    </section>
  );
};
