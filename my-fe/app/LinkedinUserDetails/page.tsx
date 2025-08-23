"use client";
import { useState } from "react";
// import { useRouter } from "next/router";
import React from "react";
// import { hash } from "bcrypt";
import crypto from "crypto-js";
import { useRouter } from "next/navigation";

export default function LinkedinUserDetailsPage() {
    const router = useRouter();
    const [ data , setData] = useState({
        username :"",
        Password : ""
    })

    function HandleLogin(): React.MouseEventHandler<HTMLButtonElement> {
        return (e) => {
            e.preventDefault();
            console.log("Logging in with:", data);
            // const  Username = hash(data.username, 10);
            // const Password =hash(data.Password, 10);
            const  Username = crypto.SHA256(data.username).toString();
            const Password = crypto .SHA256(data.Password).toString();
            
            // sessionStorage.setItem("linkedinUser", JSON.stringify(data.username));
            // sessionStorage.setItem("linkedinPassword", JSON.stringify(data.Password));
            sessionStorage.setItem("hashedLinkedinUser", JSON.stringify(Username));
            sessionStorage.setItem("hashedLinkedinPassword", JSON.stringify(Password));
            router.push("/");
            // alert("Linkedin details saved in session storage.");
        };
        
    }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <h1 className="text-3xl font-bold mb-6">LinkedIn User Details</h1>
      <p className="text-lg text-gray-700">
        This is a placeholder for LinkedIn user details.
      </p>
        <div className="mt-6 p-4 bg-white rounded shadow-md w-96">
            <label className="block mb-2 text-sm font-medium text-gray-700">
            Username:
            </label>
            <input
            type="text"
            className="w-full p-2 border border-gray-300 rounded mb-4"
            placeholder="Enter your LinkedIn username"
            value={data.username}
            onChange={(e) => setData({...data, username : e.target.value})}
            />
            <label className="block mb-2 text-sm font-medium text-gray-700">
            Password:
            </label>
            <input
            type="password"
            className="w-full p-2 border border-gray-300 rounded mb-4"
            placeholder="Enter your LinkedIn password"
            value={data.Password}
            onChange={(e) => setData({...data, Password : e.target.value})}
            />
            <button  onClick={HandleLogin()}  className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600 ">
            Submit
            </button>
        </div>
    </div>
  );
}