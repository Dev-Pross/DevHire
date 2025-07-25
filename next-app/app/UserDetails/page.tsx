"use client";

import axios from "axios";
import React, { useEffect, useState } from "react";

// Define a type for the user object returned from the API
type User = {
  id: string;
  name: string;
  email: string;
};

export default function GetDetails() {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await axios.get<User>("/api/UserDetails", {
          withCredentials: true,
        });
        setUser(res.data);
      } catch (err: any) {
        setError(err?.response?.data?.error || "Failed to fetch user details");
      }
    };

    fetchUser();
  }, []);

  return (
    <div>
      {error ? (
        <p style={{ color: "red" }}>Error: {error}</p>
      ) : user ? (
        <div>
          <h2>User Details</h2>
          <p>
            <strong>ID:</strong> {user.id}
          </p>
          <p>
            <strong>Name:</strong> {user.name}
          </p>
          <p>
            <strong>Email:</strong> {user.email}
          </p>
        </div>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}
