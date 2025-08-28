"use client";
import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { supabase } from "../utiles/supabaseClient";
import Image from "next/image";
import getLoginUser from "../utiles/getUserData";
const Navbar = () => {
  const [user, setUser] = React.useState<any>(null);
  const [open,setOpen] = useState<boolean>(false)
  const dropdownRef = useRef<HTMLDivElement>(null);;

  useEffect(() => {

    
    async function fetchUser() {
      const {data, error }= await getLoginUser();
      if (data) setUser(data?.user.user_metadata);
    }
    fetchUser();

    function handleClickOutside(event: { target: any; }) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);


  }, []);

  console.log("navbar user", user);
  return (
    <div className="sticky top-0 w-full backdrop-blur-xl z-50 navbar h-15">
      <nav className="flex justify-between items-center text-white gap-4 p-4 h-full">
        <div className="">logo</div>
        <div className="flex gap-4">
          <Link className="text-white hover:text-gray-300 font-bold" href="#">
            Home
          </Link>
          <Link className="text-white hover:text-gray-300 font-bold" href="#">
            Pricing
          </Link>
          <div className="relative group" ref={dropdownRef}>
            <div className="text-white hover:text-gray-300 font-bold cursor-pointer" 
                onClick={()=>setOpen(!open)}>
              Products
            </div>

            <div onMouseEnter={() => setOpen(true)}
                onMouseLeave={() => setOpen(false)}
                className={`absolute mt-2 w-40 bg-[#052718] rounded shadow-lg transition-opacity duration-200 ${
          open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}>
              <Link href="#" className="block px-4 py-2 text-white hover:text-gray-600 cursor-pointer">
                Tailor Resume
              </Link>
              <Link href="#" className="block px-4 py-2 text-white hover:text-gray-600 cursor-pointer">
                Perfect Titles
              </Link>
            </div>
          </div>
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
