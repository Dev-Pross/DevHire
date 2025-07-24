"use client";
import { SessionProvider, signIn, signOut, useSession } from "next-auth/react";
import { FaHome, FaBriefcase, FaFlask } from "react-icons/fa";

export function NavBar() {
  const session = useSession();

  return (
    <nav className="w-full flex justify-center mt-8">
      <div className="flex w-full max-w-5xl items-center justify-between rounded-3xl border border-white/20 bg-white/10 backdrop-blur-lg shadow-2xl px-10 py-4 transition-all duration-500 hover:shadow-[0_12px_40px_0_rgba(31,38,135,0.25)]">
        <ul className="flex space-x-2 md:space-x-4">
          <NavItem href="/" icon={<FaHome />} label="Home" />
          <NavItem href="/jobs" icon={<FaBriefcase />} label="Jobs" />
          <NavItem href="/research" icon={<FaFlask />} label="Research" />
        </ul>
        <div>
          {session.status === "authenticated" && (
            <div className="flex items-center space-x-4">
              <span className="text-white/80 font-medium text-lg hidden md:inline transition-all duration-300">
                {session.data?.user?.name
                  ? `Hi, ${session.data.user.name.split(" ")[0]}`
                  : session.data?.user?.email}
              </span>
              <button
                className="px-6 py-2 rounded-full bg-gradient-to-r from-black/80 via-gray-900 to-gray-700 text-white font-semibold shadow-lg border border-white/10 hover:bg-white hover:text-black hover:shadow-xl transition-all duration-300"
                onClick={() => signOut()}
              >
                Sign Out
              </button>
            </div>
          )}

          {session.status === "unauthenticated" && (
            <button
              className="px-6 py-2 rounded-full bg-white/90 text-black font-semibold shadow-lg border border-white/20 hover:bg-black hover:text-white hover:shadow-xl transition-all duration-300"
              onClick={() => signIn()}
            >
              Get Started
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}

// NavItem component for pretty nav links with icons and transitions
function NavItem({
  href,
  icon,
  label,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <li>
      <a
        href={href}
        className="flex items-center gap-2 px-5 py-2 rounded-xl text-white/90 font-medium text-lg transition-all duration-300 hover:bg-white/90 hover:text-black hover:scale-105 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-white/40"
      >
        <span className="text-xl">{icon}</span>
        <span className="hidden sm:inline">{label}</span>
      </a>
    </li>
  );
}

export function RealNavBar() {
  return (
    <SessionProvider>
      <NavBar />
    </SessionProvider>
  );
}
