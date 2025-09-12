  "use client";
  import React, { CSSProperties, useEffect, useRef, useState } from "react";
  import Link from "next/link";
  import { supabase } from "../utiles/supabaseClient";
  import Image from "next/image";
  import getLoginUser from "../utiles/getUserData";
  import { useRouter } from "next/navigation";
  import toast from "react-hot-toast";

  const WHITE_BG_SECTIONS = ["pricing-section","pricing-card"];
  const Navbar = () => {
    const [user, setUser] = React.useState<any>(null);
    const ref = useRef<HTMLDivElement>(null);
    const [height, setHeight] = useState(0);
    const [color, setColor] = useState("white");
    const [open,setOpen] = useState<boolean>(false)
    const [ id, setId ] = useState<any|null>(null)
    const [ resume, setResume ] = useState<any|null>(null)
    const [top, setTop] = useState<number>(0)
    const dropdownRef = useRef<HTMLDivElement>(null);

    const router = useRouter()

    useEffect(() => {
        const resume_url = sessionStorage.getItem("resume");
        async function getResume() {
          const { data, error } = await getLoginUser();
          // console.log("session ", data);
          if (error) {
            // console.error("Error fetching user:", error);
            toast.error(`Error fetching user: ${error}` )
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
            // console.log("mydata", resume_data.user.resume_url);
            if (!resume_url){
              sessionStorage.setItem("resume", resume_data.user.resume_url);
              setResume(resume_data.user.resume_url);
            }
            else setResume(resume_url)
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
          if (entry.target.id === "pricing-section"){
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

    
    const navbarStyle: CSSProperties = {
      position: "sticky",
      top: 0,
      width: "100%",
      backdropFilter: "blur(10px)",
      zIndex: 50,
      transition: " 0.3s ease",
      height: "60px", // Increased height for better visibility
    };

    const navLinkStyle:CSSProperties =  {
      color: color,
      textDecoration: "none",
      fontFamily: "'Poppins', sans-serif",
      fontWeight: 600,
      textTransform: "uppercase",
      letterSpacing: "1px",
      padding: "10px 15px",
      transition: "color 0.3s ease",
    };

    const hoverStyle = {
      color: "#00ffcc",
    };

    function logoutHandler() {
      console.log("Are you sure to logout!!");
      setTimeout(async()=>{
        setUser(null)
        sessionStorage.clear()
        const {error} = await supabase.auth.signOut()
        if(error) console.log("error in loggin out: ",error);
        window.location.href = "/"
      },1000)
    }

    return (
      <div className="navbar" style={navbarStyle}  ref={ref}>
        <nav className="flex justify-between items-center gap-6 p-4 h-full max-w-7xl mx-auto">
          <div className="rounded-full overflow-hidden">
            <Image
              src="/logo.jpg"
              alt="Icon"
              width={50}
              height={50}
              className="object-cover"
            />
          </div>
          <div className="flex gap-6">
            <Link
              href="/"
              className="hover:text-gray-300 font-bold navlink"
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
              className="hover:text-gray-300 font-bold navlink"
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
              className="hover:text-gray-300 font-bold navlink"
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
              className="hover:text-gray-300 font-bold navlink"
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
          {!user ? (
            <Link
              href="/login"
              className="cursor-pointer bg-gradient-to-r from-[#FFFF00] to-[#FFD700] font-[Poppins] text-black font-bold hover:bg-gradient-to-r hover:from-[#FF6B35] hover:to-[#F7931E] hover:text-white transition-all duration-300 hover:scale-110 hover:shadow-2xl  px-8 py-2 rounded-lg transition-colors"
              // style={{ ...navLinkStyle, padding: "6px 12px" }}
            >
              Get Started
            </Link>
          ) : (
            <div className={`bg-white w-20 rounded-4xl relative`}
            ref={dropdownRef}>
            <div className="rounded-full flex items-center pr-3 justify-between overflow-hidden relative" 
            onClick={()=>setOpen(!open)}
            onMouseEnter={() => setOpen(true)}
            // onMouseLeave={() => setOpen(!open)}
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
            <div className={`absolute top-16 left-1/2 transform -translate-x-1/2 p-3 w-50 bg-white/50 backdrop-blur rounded-lg shadow-lg z-50 transition-opacity duration-200 ${
        open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}`}
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
          
        </nav>
      </div>
    );
  };

  export default Navbar;
