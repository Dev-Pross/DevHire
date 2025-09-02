"use client";
import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { supabase } from "../utiles/supabaseClient";
import Image from "next/image";
import getLoginUser from "../utiles/getUserData";
const Navbar = () => {
  const [user, setUser] = React.useState<any>(null);

  useEffect(() => {

    
    async function fetchUser() {
      const {data, error }= await getLoginUser();
      if (data) {
        setUser(data?.user.user_metadata);
        console.log(data?.user.user_metadata);
        
      }
 
    }
    fetchUser();
    console.log(user);
    
    


  }, []);
  return (
    <div className={`sticky top-0 w-full backdrop-blur-xl z-50 navbar h-15 invert-none`}>
      <nav className="flex justify-between items-center text-white gap-4 p-4 h-full">
        <div className="">logo</div>
        <div className="flex gap-4">
          <Link className="text-white hover:text-gray-300 font-bold" href="#">
            Home
          </Link>
          <Link className="text-white hover:text-gray-300 font-bold" href="#">
            Pricing
          </Link>
          <Link className="text-white hover:text-gray-300 font-bold" href="#">
            Tailor Resume
          </Link>

          <Link className="text-white hover:text-gray-300 font-bold" href="#">
            About us
          </Link>
        </div>
        {!user ? (
          <Link href="/login" className="rounded-4xl pl-4 pr-4 border-2 p-1">
            Get Started
          </Link>
        ) : (
          <div className="pl-4 pr-4 ">
            {/* {user ? ( */}
            <Image
              src={"/profile.svg"}
              alt="Profile Icon"
              width={50}
              height={50}
            ></Image>
          </div>
        )}
      </nav>
    </div>
  );
};

export default Navbar;
