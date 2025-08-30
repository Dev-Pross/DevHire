"use client";
import { useEffect, useState } from "react";
import Login from "./Components/Login";
import Navbar from "./Components/Navbar";
import Register from "./Components/Register";
import { supabase } from "./utiles/supabaseClient";
import Jobs from "./Components/Jobs";
import { HeroTalent } from "./Components/Landing-Page/hero-section";
import Apply from "./Components/Apply";
import UploadButton from "./UploadButton/page";
import getLoginUser from "./utiles/getUserData";
// import HeroTalent from "./Components/Landing-Page/HeroTalent";
export default function Home() {
  const data = {
    email: "",
    user: "",
  };
  const [user, setUser] = useState(data);

  useEffect(() => {
    async function fetchSession() {
      const { data, error } = await getLoginUser();
      console.log("session ", data);
      if (error) {
        console.error("Error fetching user:", error);
      } else if (data?.user) {
        console.log(
          "User is logged in:",
          data?.user.user_metadata.email,
          " ",
          data?.user.user_metadata.username
        );
        setUser({
          email: data?.user.user_metadata.email,
          user: data?.user.user_metadata.username,
        });
        sessionStorage.setItem("id",data?.user.user_metadata.sub)
        sessionStorage.setItem("name",data?.user.user_metadata.username)
        sessionStorage.setItem("email",data?.user.user_metadata.email)

      } else {
        console.log("No user is logged in.");
      }
    }
    fetchSession();
  }, []);

  return (
    <div
      style={{
        minHeight: "100vh",
      }}
    >
      <Navbar />
      <div style={{ flex: 1 }}>
        {/* <Login />
        < Register /> */}
        {/* <Jobs url={ url } userId={ userid} password={password} />
        <> */}
        {/* <Apply/>
         */}
        {/* <UploadButton/> */}
        <HeroTalent />
      </div>
    </div>
  );
}
