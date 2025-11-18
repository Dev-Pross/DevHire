"use client";
import React, { CSSProperties, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { supabase } from "../utiles/supabaseClient";
import Image from "next/image";
import getLoginUser from "../utiles/getUserData";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";

const WHITE_BG_SECTIONS = ["pricing-section", "pricing-card"];
const Navbar = () => {
  const [user, setUser] = React.useState<any>(null);
  const ref = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState(0);
  const [color, setColor] = useState("white");
  const [open, setOpen] = useState<boolean>(false)
  const [id, setId] = useState<any | null>(null)
  const [resume, setResume] = useState<any | null>(null)
  const [top, setTop] = useState<number>(0)
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const router = useRouter()

  useEffect(() => {
    const resume_url = sessionStorage.getItem("resume");
    async function getResume() {
      const { data, error } = await getLoginUser();
      // console.log("session ", data);
      if (error) {
        // console.error("Error fetching user:", error);
        toast.error(`Error fetching user: ${error}`)
      } else if (data?.user) {
        console.log("loggedin");
      } else {
        console.log("No user is logged in.");
        // toast.error("")
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
        console.log("mydata", resume_data.user.linkedin_context);
        if (!resume_url) {
          sessionStorage.setItem("resume", resume_data.user.resume_url);
          
          setResume(resume_data.user.resume_url);
          console.log(resume_data.user.resume_url);
          
        }
        
        else setResume(resume_url)
        if(resume_data.user.linkedin_context){
            sessionStorage.setItem("Lcontext", "true")
            console.log("context created - true")
          }
          else{
            sessionStorage.setItem("Lcontext", "false")
            console.log("context created - true")
          }
      }
    }
    getResume();
  }, [id]);

  useEffect(() => {
    async function fetchUser() {
      const { data, error } = await getLoginUser();
      if (data) {
        setUser(data?.user.user_metadata);
      }
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


  useEffect(() => {
    if (ref.current) {
      setHeight(ref.current.offsetHeight);
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        setTop(entry.boundingClientRect.top);

        // Only change color when actually intersecting with sufficient threshold
        if (entry.isIntersecting) {
          if (entry.target.id === "pricing-section") {
            // console.log("White background section:", entry.target.id);
            setColor("black");
          }
          else if (entry.target.id === "pricing-card") {
            // console.log("White background section:", entry.target.id);
            setColor("white");
          } else {
            // console.log("Dark background section:", entry.target.id);
            setColor("white");
          }
        } else {
          // When not intersecting, check if we should return to default (white)
          if (entry.target.id === "pricing-card" || entry.target.id === "pricing-section") {
            setColor("white"); // Return to white when leaving white sections
          }
        }

        // console.log("top:", entry.boundingClientRect.top);
        // console.log("height:", height);
        // console.log("isIntersecting:", entry.isIntersecting);
      },
      {
        threshold: 0.9,
        rootMargin: `-${height}px 0px 0px 0px`,
      }
    );

    WHITE_BG_SECTIONS.forEach((id) => {
      const target = document.getElementById(id);
      if (target) observer.observe(target);
    });

    return () => observer.disconnect();
  }, [height]);


  const navbarStyle:CSSProperties = {
    position: "sticky",
    top: 0,
    width: "100%",
    backdropFilter: "blur(10px)",
    zIndex: 50,
    transition: "all 0.3s ease",
  };

  const navLinkStyle :CSSProperties= {
    color: color,
    textDecoration: "none",
    fontFamily: "'Poppins', sans-serif",
    fontWeight: 600,
    textTransform: "uppercase" as const,
    letterSpacing: "1px",
    padding: "10px 15px",
    transition: "color 0.3s ease",
  };

  const hoverStyle = {
    color: "#00ffcc",
  };

  function logoutHandler() {
    console.log("Are you sure to logout!!");
    setTimeout(async () => {
      setUser(null)
      sessionStorage.clear()
      const { error } = await supabase.auth.signOut()
      if (error) console.log("error in loggin out: ", error);
      window.location.href = "/"
    }, 1000)
  }

  return (
    <div className="navbar min-h-[60px]" style={navbarStyle} ref={ref}>
      <nav className="flex justify-between items-center px-4 py-3 lg:px-8 max-w-7xl mx-auto" style={navbarStyle}>
        {/* Logo */}
        <Link href="/" className="rounded-full overflow-hidden flex-shrink-0">
          <Image
            src="/logo.jpg"
            alt="Icon"
            width={50}
            height={50}
            className="object-cover"
          />
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden lg:flex gap-6 items-center">
          <Link 
            href="/"
            className="hover:text-gray-300 font-bold transition-colors duration-300"
            style={navLinkStyle}
            onMouseEnter={(e) =>
              ((e.target as HTMLAnchorElement).style.color = hoverStyle.color)
            }
            onMouseLeave={(e) =>
              ((e.target as HTMLAnchorElement).style.color = color)
            }
          >
            Home
          </Link>
          <Link
            href="/pricing"
            className="hover:text-gray-300 font-bold transition-colors duration-300"
            style={navLinkStyle}
            onMouseEnter={(e) =>
              ((e.target as HTMLAnchorElement).style.color = hoverStyle.color)
            }
            onMouseLeave={(e) =>
              ((e.target as HTMLAnchorElement).style.color = color)
            }
          >
            Pricing
          </Link>
          <Link
            href="/Jobs/tailor"
            className="hover:text-gray-300 font-bold transition-colors duration-300"
            style={navLinkStyle}
            onMouseEnter={(e) =>
              ((e.target as HTMLAnchorElement).style.color = hoverStyle.color)
            }
            onMouseLeave={(e) =>
              ((e.target as HTMLAnchorElement).style.color = color)
            }
          >
            Tailor Resume
          </Link>
          <Link
            href="/about"
            className="hover:text-gray-300 font-bold transition-colors duration-300"
            style={navLinkStyle}
            onMouseEnter={(e) =>
              ((e.target as HTMLAnchorElement).style.color = hoverStyle.color)
            }
            onMouseLeave={(e) =>
              ((e.target as HTMLAnchorElement).style.color = color)
            }
          >
            About us
          </Link>
        </div>

        {/* Desktop User Actions */}
        <div className="hidden lg:flex items-center">
          {!user ? (
            <Link
              href="/login"
              className="cursor-pointer bg-gradient-to-r from-[#FFFF00] to-[#FFD700] font-[Poppins] text-black font-bold hover:from-[#FF6B35] hover:to-[#F7931E] hover:text-white transition-all duration-300 hover:scale-110 hover:shadow-2xl px-8 py-2 rounded-lg"
            >
              Get Started
            </Link>
          ) : (
            <div className={`bg-white w-20 rounded-4xl relative`} ref={dropdownRef}>
              <div className="rounded-full flex items-center pr-3 justify-between overflow-hidden relative cursor-pointer"
                onClick={() => setOpen(!open)}
                onMouseEnter={() => setOpen(true)}
              >
                <Image
                  src="/profile.svg"
                  alt="Profile Icon"
                  width={50}
                  height={50}
                  className="object-cover"
                />
                <p className={`text-black transform transition-transform ${open ? 'rotate-180' : ''}`}>
                  ⏷
                </p>
              </div>
              <div className={`absolute top-16 left-1/2 transform -translate-x-1/2 p-3 w-50 bg-white/50 backdrop-blur rounded-lg shadow-lg z-50 transition-opacity duration-200 ${open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}`}
                onMouseEnter={() => setOpen(true)}
                onMouseLeave={() => setOpen(false)}>
                <ul className="">
                  <Link href={"/Jobs/profile"}>
                    <li className="bg-transparent backdrop-blur hover:bg-gray-100 cursor-pointer rounded-lg text-center p-1 mb-2">Profile</li>
                  </Link>
                  <li className="bg-transparent backdrop-blur hover:bg-gray-100 cursor-pointer rounded-lg text-center p-1" onClick={logoutHandler}>Logout</li>
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Mobile Hamburger Menu */}
        <button
          className="lg:hidden flex flex-col gap-1.5 p-2"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle mobile menu"
        >
          <span style={{backgroundColor: color}} className={`h-0.5 w-6 transition-all duration-300 ${mobileMenuOpen ? 'rotate-45 translate-y-2' : ''}`}></span>
          <span style={{backgroundColor: color}} className={`h-0.5 w-6 transition-all duration-300 ${mobileMenuOpen ? 'opacity-0' : ''}`}></span>
          <span style={{backgroundColor: color}} className={`h-0.5 w-6 transition-all duration-300 ${mobileMenuOpen ? '-rotate-45 -translate-y-2' : ''}`}></span>
        </button>
      </nav>

      {/* Mobile Menu */}
      <div className={`lg:hidden bg-black/95 backdrop-blur-lg transition-all duration-300 ${mobileMenuOpen ? 'max-h-screen opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
        <div className="flex flex-col gap-4 p-6">
          <Link 
            href="/"
            className="text-white hover:text-[#00ffcc] font-bold text-lg transition-colors"
            onClick={() => setMobileMenuOpen(false)}
          >
            Home
          </Link>
          <Link
            href="/pricing"
            className="text-white hover:text-[#00ffcc] font-bold text-lg transition-colors"
            onClick={() => setMobileMenuOpen(false)}
          >
            Pricing
          </Link>
          <Link
            href="/Jobs/tailor"
            className="text-white hover:text-[#00ffcc] font-bold text-lg transition-colors"
            onClick={() => setMobileMenuOpen(false)}
          >
            Tailor Resume
          </Link>
          <Link
            href="/about"
            className="text-white hover:text-[#00ffcc] font-bold text-lg transition-colors"
            onClick={() => setMobileMenuOpen(false)}
          >
            About us
          </Link>
          
          {!user ? (
            <Link
              href="/login"
              className="bg-gradient-to-r from-[#FFFF00] to-[#FFD700] text-black font-bold py-3 px-6 rounded-lg text-center hover:from-[#FF6B35] hover:to-[#F7931E] hover:text-white transition-all"
              onClick={() => setMobileMenuOpen(false)}
            >
              Get Started
            </Link>
          ) : (
            <div className="flex flex-col gap-3 border-t border-white/20 pt-4">
              <Link href={"/Jobs/profile"} onClick={() => setMobileMenuOpen(false)}>
                <button className="w-full bg-white/10 hover:bg-white/20 text-white font-bold py-3 px-6 rounded-lg transition-all">
                  Profile
                </button>
              </Link>
              <button 
                className="w-full bg-red-500/80 hover:bg-red-600 text-white font-bold py-3 px-6 rounded-lg transition-all"
                onClick={() => {
                  setMobileMenuOpen(false);
                  logoutHandler();
                }}
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Navbar;
