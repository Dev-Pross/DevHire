"use client";
import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { supabase } from "../utiles/supabaseClient";
import Image from "next/image";
import getLoginUser from "../utiles/getUserData";


const WHITE_BG_SECTIONS = ["features-section", "pricing-section"];
const Navbar = () => {
  const [user, setUser] = React.useState<any>(null);
  const ref = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState(0);
  const [color, setColor] = useState("white")

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

  useEffect(()=>{
  if (ref.current) {
    setHeight(ref.current.offsetHeight);
    }
    const observer = new IntersectionObserver(
    ([entry]) => {
      const top = entry.boundingClientRect.top;

      if (entry.isIntersecting && top <= height) {
        // Features section top is overlapped with navbar -> set black
        setColor("black");
      } else if (top > height) {
        // Features section top is below navbar -> set white
        setColor("white");
      }
    },
    {
      threshold: 0,
      rootMargin: `-${height}px 0px 0px 0px`
    }
  );


  WHITE_BG_SECTIONS.forEach(id=>{

      const target = document.getElementById(id);
      if(target) observer.observe(target);
    })

  return () => observer.disconnect()
  },[])
  return (
    <div className={`sticky top-0 w-full backdrop-blur-xl z-50 navbar text-${color} transition-colors delay-100 h-15 invert-none`} ref={ref}>
      <nav className="flex justify-between items-center  gap-4 p-4 h-full">
        <div className="rounded-full overflow-hidden">
          <Image
              src={"/logo.jpeg"}
              alt="Icon"
              width={50}
              height={50}
              className=""
            ></Image>
        </div>
        <div className="flex gap-4">
          <Link className=" hover:text-gray-300 font-bold" href="#">
            Home
          </Link>
          <Link className=" hover:text-gray-300 font-bold" href="#">
            Pricing
          </Link>
          <Link className=" hover:text-gray-300 font-bold" href="#">
            Tailor Resume
          </Link>

          <Link className=" hover:text-gray-300 font-bold" href="#">
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
