"use client";
import { SessionProvider, signIn, signOut, useSession } from "next-auth/react";

export function NavBar() {
  const session = useSession();

  return (
    <>
      <div className="flex flex col border-2  rounded-2xl justify-between m-4 p-4 mx-40 my-8 ">
        <div>
          <ul className="flex space-x-4">
            <li className="hover:bg-white hover:rounded-lg p-4 m-2 hover:text-black">
              Home
            </li>
            <li className="hover:bg-white hover:rounded-lg p-4 m-2 hover:text-black">
              Jobs
            </li>
            <li className="hover:bg-white hover:rounded-lg p-4 m-2 hover:text-black">
              Research
            </li>
          </ul>
        </div>
        <div>
          {session.status === "authenticated" && (
            <div>
              <button
                className="hover:bg-white hover:rounded-lg p-4 m-2 hover:text-black"
                onClick={() => signOut()}
              >
                Sign Out
              </button>
            </div>
          )}

          {session.status === "unauthenticated" && (
            <div>
              <button
                className="hover:bg-white hover:rounded-lg p-4 m-2 hover:text-black"
                onClick={() => signIn()}
              >
                {" "}
                Get Started
              </button>
            </div>
          )}
        </div>
      </div>
      <div className="items-center h-screen w-screen flex justify-center ">
        <h1>Hello world </h1>
      </div>
    </>
  );
}

export function RealNavBar() {
  return (
    <SessionProvider>
      <NavBar />
    </SessionProvider>
  );
}
