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
  const [color, setColor] = useState("white");

  useEffect(() => {
    async function fetchUser() {
      const { data, error } = await getLoginUser();
      if (data) {
        setUser(data?.user.user_metadata);
      }
    }
    fetchUser();
  }, []);

  useEffect(() => {
    if (ref.current) {
      setHeight(ref.current.offsetHeight);
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        const top = entry.boundingClientRect.top;

        if (entry.isIntersecting && top <= height) {
          setColor("black");
        } else if (top > height) {
          setColor("white");
        }
      },
      {
        threshold: 0,
        rootMargin: `-${height}px 0px 0px 0px`,
      }
    );

    WHITE_BG_SECTIONS.forEach((id) => {
      const target = document.getElementById(id);
      if (target) observer.observe(target);
    });

    return () => observer.disconnect();
  }, []);

  const navbarStyle = {
    position: "sticky",
    top: 0,
    width: "100%",
    backdropFilter: "blur(10px)",
    zIndex: 50,
    transition: "color 0.3s ease",
    height: "60px", // Increased height for better visibility
    color: color,
  };

  const navLinkStyle = {
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

  return (
    <div className="navbar" style={navbarStyle} ref={ref}>
      <nav className="flex justify-between items-center gap-6 p-4 h-full max-w-7xl mx-auto">
        <div className="rounded-full overflow-hidden">
          <Image
            src="/logo.jpeg"
            alt="Icon"
            width={50}
            height={50}
            className="object-cover"
          />
        </div>
        <div className="flex gap-6">
          <Link
            href="#"
            className="hover:text-gray-300 font-bold"
            style={navLinkStyle}
            onMouseEnter={(e) => (e.target as HTMLAnchorElement).style.color = hoverStyle.color}
            onMouseLeave={(e) => (e.target as HTMLAnchorElement).style.color = color}
          >
            Home
          </Link>
          <Link
            href="#"
            className="hover:text-gray-300 font-bold"
            style={navLinkStyle}
            onMouseEnter={(e) => (e.target as HTMLAnchorElement).style.color = hoverStyle.color}
            onMouseLeave={(e) => (e.target as HTMLAnchorElement).style.color = color}
          >
            Pricing
          </Link>
          <Link
            href="#"
            className="hover:text-gray-300 font-bold"
            style={navLinkStyle}
            onMouseEnter={(e) => (e.target as HTMLAnchorElement).style.color = hoverStyle.color}
            onMouseLeave={(e) => (e.target as HTMLAnchorElement).style.color = color}
          >
            Tailor Resume
          </Link>
          <Link
            href="#"
            className="hover:text-gray-300 font-bold"
            style={navLinkStyle}
            onMouseEnter={(e) => (e.target as HTMLAnchorElement).style.color = hoverStyle.color}
            onMouseLeave={(e) => (e.target as HTMLAnchorElement).style.color = color}
          >
            About us
          </Link>
        </div>
        {!user ? (
          <Link
            href="/login"
            className="rounded-full pl-4 pr-4 border-2 border-white p-2 hover:bg-white hover:text-black transition-colors duration-300"
            style={{ ...navLinkStyle, padding: "6px 12px" }}
          >
            Get Started
          </Link>
        ) : (
          <div className="rounded-full overflow-hidden">
            <Image
              src="/profile.svg"
              alt="Profile Icon"
              width={50}
              height={50}
              className="object-cover"
            />
          </div>
        )}
      </nav>
    </div>
  );
};

export default Navbar;