"use client";
import Link from "next/link";
// import { signIn, signOut ,  } from "next-auth/react";
import { useSession, signIn, signOut, SessionProvider } from "next-auth/react";
export  function NavBar() {
  const { data: session } = useSession();
  return (
    <div className="flex flex-col  justify-between">
      <nav className="flex justify-between  border border-gray-200 p-8 m-4  mx-40 rounded-xl">
        <div className="flex gap-4">
          <Link href="/">Home</Link>
          <Link href="/about">About</Link>
          <Link href="/contact">Contact</Link>
          <Link href="/jobs">Jobs</Link>
        </div>

        <div className="flex gap-4 ">
          {session ? (
            <button
              className="hover:bg-white rounded-lg p-2 px-4 hover:text-black"
              onClick={() => signOut()}
            >
              {" "}
              Signout{" "}
            </button>
          ) : (
            <button
              className="hover:bg-white rounded-lg p-2 px-4 hover:text-black"
              onClick={() => signIn()}
            >
              Signin
            </button>
          )}
        </div>
      </nav>
      <div className="flex flex-col items-center justify-center h-screen space-y-4">
        <h4>Welcome o this owrld </h4>
        <h1 className="text-4xl font-bold">Welcome to the Home Page</h1>
        <p className="text-lg">This is the home page the of the website.</p>
      </div>
    </div>
  );
}
export function RealNavBar(){

    return(
        <SessionProvider>
        <NavBar/>
    </SessionProvider>
    )
}