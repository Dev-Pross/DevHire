"use client";

import axios from "axios";
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

// Define a type for the user object returned from the API
type User = {
  id: string;
  name: string;
  email: string;
};

export default function GetDetails() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [redirecting, setRedirecting] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await axios.get<User>("/api/UserDetails", {
          withCredentials: true,
          validateStatus: () => true, // Accept all status codes
        });

        // If the API responded with a redirect (302/307), or 401/403, handle it
        if (
          res.status === 401 ||
          res.status === 403 ||
          (res.request?.responseURL && res.request.responseURL.includes("/signin")) ||
          (res.status >= 300 && res.status < 400)
        ) {
          setRedirecting(true);
          router.replace("/signin");
          return;
        }

        // If user not found
        if (res.status === 404) {
          setUser(null);
          setLoading(false);
          return;
        }

        // If success
        if (res.status === 200 && res.data) {
          setUser(res.data);
          setLoading(false);
        } else {
          setUser(null);
          setLoading(false);
        }
      } catch (err: any) {
        setUser(null);
        setLoading(false);
        setRedirecting(true);
        router.replace("/signin");
      }
    };

    fetchUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  // If still loading, render nothing (or a spinner if you want)
  if (loading || redirecting) {
    return null;
  }

  // If user details exist, print them
  if (user) {
    return (
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
    );
  }

  // If user is null, the redirect will happen, so render nothing
  return null;
}
