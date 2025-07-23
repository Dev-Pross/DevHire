"use client";
import React, { useState } from "react";
import Link from "next/link";
import axios from "axios";

export default function SignUp() {
  const [data, setData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (data.password !== data.confirmPassword) {
      setError("Passwords don't match");
      return;
    }
    setLoading(true);
    try {
      // Let the server handle password hashing for security
      const res = await axios.post("/api/signup", {
        username: data.username,
        email: data.email,
        password: data.password,
      });
      // Optionally, handle success (e.g., redirect or show message)
      // Reset form or show success message here
         // Optionally, handle success (e.g., redirect or show message)
      // Reset form or show success message here
    } catch (err) {
      setError("An error occurred during signup.");
      console.log(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <input
          type="text"
          name="username"
          placeholder="Enter Your Name"
          value={data.username}
          onChange={handleChange}
          required
        />
        <input
          type="email"
          name="email"
          placeholder="Enter Your Email"
          value={data.email}
          onChange={handleChange}
          required
        />
        <input
          type="password"
          name="password"
          placeholder="Enter Your Password"
          value={data.password}
          onChange={handleChange}
          required
        />
        <input
          type="password"
          name="confirmPassword"
          placeholder="Confirm Your Password"
          value={data.confirmPassword}
          onChange={handleChange}
          required
        />

        <button type="submit" disabled={loading}>
          {loading ? "Submitting..." : "Submit"}
        </button>

        {error && (
          <div style={{ color: "red", marginTop: "8px" }}>{error}</div>
        )}

        <Link href="signin">SignIn</Link>
      </div>
    </form>
  );
}
