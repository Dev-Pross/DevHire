"use client";
import { useEffect, useState } from "react";
import Navbar from "./Components/Navbar";
import { HeroTalent } from "./Components/Landing-Page/hero-section";
import getLoginUser from "./utiles/getUserData";

export default function Home() {

  // const [user, setUser] = useState<any>();

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
        // setUser(data.user.user_metadata);
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
