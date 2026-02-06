"use client";
import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { supabase } from "../utiles/supabaseClient";
import Image from "next/image";
import getLoginUser from "../utiles/getUserData";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";

const Navbar = () => {
  const [user, setUser] = React.useState<any>(null);
  const [open, setOpen] = useState<boolean>(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [id, setId] = useState<any | null>(null);
  const [resume, setResume] = useState<any | null>(null);
  const [scrolled, setScrolled] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    const resume_url = sessionStorage.getItem("resume");
    async function getResume() {
      const { data, error } = await getLoginUser();
      if (error) {
        toast.error(`Error fetching user: ${error}`);
      } else if (data?.user) {
        console.log("loggedin");
      } else {
        console.log("No user is logged in.");
      }
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
        if (!resume_url) {
          sessionStorage.setItem("resume", resume_data.user.resume_url);
          setResume(resume_data.user.resume_url);
        } else setResume(resume_url);
        if (resume_data.user.linkedin_context) {
          sessionStorage.setItem("Lcontext", "true");
        } else {
          sessionStorage.setItem("Lcontext", "false");
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

    function handleClickOutside(event: { target: any }) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);

    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  function logoutHandler() {
    setTimeout(async () => {
      setUser(null);
      sessionStorage.clear();
      const { error } = await supabase.auth.signOut();
      if (error) console.log("error in logging out: ", error);
      window.location.href = "/";
    }, 1000);
  }

  const navLinks = [
    { href: "/", label: "Home" },
    { href: "/Jobs/tailor", label: "Tailor Resume" },
    { href: "/Jobs/portfolio", label: "Portfolio" },
    { href: "/about", label: "About" },
  ];

  return (
    <div
      className={`navbar sticky top-0 w-full z-50 transition-all duration-300 ${
        scrolled
          ? "bg-black/80 backdrop-blur-xl border-b border-white/[0.06]"
          : "bg-transparent"
      }`}
    >
      <nav className="flex justify-between items-center px-5 py-4 lg:px-10 max-w-7xl mx-auto">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 rounded-lg overflow-hidden group-hover:shadow-lg group-hover:shadow-emerald-500/25 transition-all duration-300">
            <Image
              src="/logo.jpg"
              alt="HireHawk Logo"
              width={36}
              height={36}
              className="w-full h-full object-cover"
              priority
            />
          </div>
          <span className="text-white font-semibold text-lg tracking-tight hidden sm:block">
            HireHawk
          </span>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden lg:flex items-center gap-1">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-gray-400 hover:text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-white/[0.05] transition-all duration-200"
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Desktop User Actions */}
        <div className="hidden lg:flex items-center gap-3">
          {!user ? (
            <div className="flex items-center gap-3">
              <Link
                href="/login"
                className="text-gray-400 hover:text-white text-sm font-medium px-4 py-2 transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="btn-primary text-sm !py-2.5 !px-6"
              >
                Get Started
              </Link>
            </div>
          ) : (
            <div className="relative" ref={dropdownRef}>
              <button
                className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/[0.05] border border-white/[0.08] hover:border-white/[0.15] transition-all cursor-pointer"
                onClick={() => setOpen(!open)}
                onMouseEnter={() => setOpen(true)}
              >
                <div className="w-7 h-7 rounded-full bg-emerald-500/20 flex items-center justify-center">
                  <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <svg className={`w-3.5 h-3.5 text-gray-400 transition-transform ${open ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              <div
                className={`absolute right-0 top-full mt-2 w-48 bg-[#1A1A1A] border border-white/[0.08] rounded-xl shadow-2xl shadow-black/50 overflow-hidden transition-all duration-200 ${
                  open ? "opacity-100 translate-y-0 pointer-events-auto" : "opacity-0 -translate-y-2 pointer-events-none"
                }`}
                onMouseEnter={() => setOpen(true)}
                onMouseLeave={() => setOpen(false)}
              >
                <Link
                  href="/Jobs/profile"
                  className="flex items-center gap-3 px-4 py-3 text-sm text-gray-300 hover:text-white hover:bg-white/[0.05] transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                  </svg>
                  Profile
                </Link>
                <button
                  onClick={logoutHandler}
                  className="w-full flex items-center gap-3 px-4 py-3 text-sm text-gray-300 hover:text-red-400 hover:bg-white/[0.05] transition-colors cursor-pointer"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
                  </svg>
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Mobile Hamburger */}
        <button
          className="lg:hidden flex flex-col gap-1.5 p-2 rounded-lg hover:bg-white/[0.05] transition-colors"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle mobile menu"
        >
          <span className={`h-0.5 w-5 bg-gray-300 rounded-full transition-all duration-300 ${mobileMenuOpen ? "rotate-45 translate-y-2" : ""}`} />
          <span className={`h-0.5 w-5 bg-gray-300 rounded-full transition-all duration-300 ${mobileMenuOpen ? "opacity-0" : ""}`} />
          <span className={`h-0.5 w-5 bg-gray-300 rounded-full transition-all duration-300 ${mobileMenuOpen ? "-rotate-45 -translate-y-2" : ""}`} />
        </button>
      </nav>

      {/* Mobile Menu */}
      <div
        className={`lg:hidden border-t border-white/[0.06] bg-[#0A0A0A]/98 backdrop-blur-xl transition-all duration-300 ${
          mobileMenuOpen ? "max-h-[500px] opacity-100" : "max-h-0 opacity-0 overflow-hidden"
        }`}
      >
        <div className="flex flex-col gap-1 p-4">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-gray-300 hover:text-white font-medium py-3 px-4 rounded-lg hover:bg-white/[0.05] transition-all"
              onClick={() => setMobileMenuOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <div className="border-t border-white/[0.06] mt-2 pt-3">
            {!user ? (
              <div className="flex flex-col gap-2">
                <Link
                  href="/login"
                  className="text-gray-300 hover:text-white font-medium py-3 px-4 rounded-lg hover:bg-white/[0.05] text-center transition-all"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  className="btn-primary text-center !rounded-lg"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Get Started
                </Link>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                <Link
                  href="/Jobs/profile"
                  className="text-gray-300 hover:text-white font-medium py-3 px-4 rounded-lg hover:bg-white/[0.05] transition-all"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Profile
                </Link>
                <button
                  className="text-red-400 hover:text-red-300 font-medium py-3 px-4 rounded-lg hover:bg-white/[0.05] text-left transition-all cursor-pointer"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    logoutHandler();
                  }}
                >
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Navbar;
