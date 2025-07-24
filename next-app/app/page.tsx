import { getServerSession } from "next-auth";
import { RealNavBar } from "./components/NavBar";
import { authoptions } from "./api/auth/[...nextauth]/route";

// Move all styling to Tailwind classes and inline styles, avoid styled-jsx or any client-only code

export default async function Home() {
  const session = await getServerSession(authoptions);

  return (
    <div
      className="min-h-screen w-full flex flex-col"
      style={{
        background:
          "linear-gradient(135deg, #18181b 0%, #23272f 60%, #f5f5f7 100%)",
      }}
    >
      <RealNavBar />
      <main className="flex flex-1 flex-col items-center justify-center px-4 py-12">
        <div className="bg-white/10 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 max-w-2xl w-full p-10 flex flex-col items-center">
          <h1 className="w-full flex flex-col items-center text-5xl font-extrabold mb-4 tracking-tight drop-shadow-lg">
            <span
              className="text-center bg-gradient-to-r from-[#C0C0C0] via-[#e5e5e5] to-[#f5f5f7] bg-clip-text text-transparent transition-all duration-700 ease-in-out"
              style={{
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              {/* Welcome */}
            </span>
            <span
              className="text-center bg-gradient-to-r from-[#f5f5f7] via-[#23272f] to-[#C0C0C0] bg-clip-text text-transparent transition-all duration-700 ease-in-out animate-gradient-x"
              style={{
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
                animation: "gradient-x 4s ease-in-out infinite",
              }}
            >
             Welcome  to Automate job 
            </span>
            <style>
              {`
                @keyframes gradient-x {
                  0%, 100% {
                    background-position: 0% 50%;
                  }
                  50% {
                    background-position: 100% 50%;
                  }
                }
                .animate-gradient-x {
                  background-size: 200% 200%;
                }
              `}
            </style>
          </h1>
          <p className="text-lg text-gray-200 mb-8 text-center max-w-xl">
            Experience a premium, modern, and minimal interface. Enjoy seamless navigation and a luxurious black &amp; white theme with subtle gradients and glassy effects.
          </p>
          {!session ? (
            <a
              href="/api/auth/signin"
              className="px-8 py-3 rounded-full bg-white/90 text-black font-semibold shadow-lg hover:bg-white transition-all duration-200"
            >
              Sign In
            </a>
          ) : (
            <div className="flex flex-col items-center">
              <span className="text-white text-xl mb-2">
                Hello, <span className="font-bold">{session.user?.name || session.user?.email}</span>
              </span>
              <a
                href="/dashboard"
                className="px-8 py-3 rounded-full bg-black/80 text-white font-semibold shadow-lg hover:bg-black transition-all duration-200 border border-white/10"
              >
                Go to Dashboard
              </a>
            </div>
          )}
        </div>
        <footer className="mt-16 text-gray-400 text-sm">
          &copy; {new Date().getFullYear()} Premium Next App. All rights reserved.
        </footer>
      </main>
    </div>
  );
}
