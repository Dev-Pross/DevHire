"use client"
import { useEffect, useState } from "react";
import Login from "./Components/Login";
import Navbar from "./Components/Navbar";
import Register from "./Components/Register";
import { supabase } from "./utiles/supabaseClient";
import Jobs from "./Components/Jobs";

export default function Home() {
  const data = {
    email:"",
    user:""
  }
  const [ user, setUser ] = useState(data)


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
        <Jobs/>
      </div>
    </div>
  );
}
