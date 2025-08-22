"use client"
import { useEffect, useState } from "react";
import Login from "./Components/Login";
import Navbar from "./Components/Navbar";
import Register from "./Components/Register";
import { supabase } from "./utiles/supabaseClient";
import Jobs from "./Components/Jobs";
import {HeroTalent} from "./Components/Landing-Page/hero-section";
import Apply from "./Components/Apply";
import UploadButton from "./UploadButton/page";
// import HeroTalent from "./Components/Landing-Page/HeroTalent";
export default function Home() {
  const data = {
    email:"",
    user:""
  }
  const [ user, setUser ] = useState(data)

    const userid="linkedinpostgenerator@gmail.com"
    const password = "mDEccH86!zmGr:_"
    const url = "https://uunldfxygooitgmgtcis.supabase.co/storage/v1/object/sign/user-resume/SRINIVAS_SAI_SARAN_TEJA%20(1).pdf?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9iZjI4OTBiZS0wYmYxLTRmNTUtOTI3Mi0xZGNiNTRmNzNhYzAiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJ1c2VyLXJlc3VtZS9TUklOSVZBU19TQUlfU0FSQU5fVEVKQSAoMSkucGRmIiwiaWF0IjoxNzU0Mzc4OTgwLCJleHAiOjE3NTY5NzA5ODB9.1unaMom_BGXfxkvFB95XUMFLw7FOoVzMDBwzrJI8mOs"


  useEffect(()=>{
    async function fetchSession()
    {
      const { data, error } = await supabase.auth.getSession();
      console.log("session ",data);
      if (error) {
        console.error("Error fetching user:", error);
      }
      else if (data.session?.user) {
        console.log("User is logged in:", data.session?.user.user_metadata.email," ", data.session?.user.user_metadata.username);
        setUser({
          email: data.session?.user.user_metadata.email,
          user: data.session?.user.user_metadata.username
        })
      } else {
        console.log("No user is logged in.");
      }
    }
    fetchSession();
  },[])



  
  return (
    <div
      style={{
        minHeight: "100vh",
      }}
    >
      <Navbar />
      <div style={{ flex: 1}}>
        {/* <Login />
        < Register /> */}
        {/* <Jobs url={ url } userId={ userid} password={password} />
        <> */}
        {/* <Apply/>
         */}
         <UploadButton/>
      </div>
    </div>
  );
}
