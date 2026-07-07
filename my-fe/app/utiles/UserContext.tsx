"use client";
import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from "react";
import { supabase } from "./supabaseClient";

interface UserData {
  id: string | null;
  email: string | null;
  name: string | null;
  resume_url: string | null;
  profile_image: string | null;
  linkedin_context: boolean;
  applied_jobs: string[];
  tier: string;
  shared_generation_credits: number;
  fetch_jobs_credits: number;
}

interface UserContextType {
  user: UserData;
  loading: boolean;
  isLoggedIn: boolean;
  refreshUser: () => Promise<void>;
  logout: () => Promise<void>;
}

const defaultUser: UserData = {
  id: null,
  email: null,
  name: null,
  resume_url: null,
  profile_image: null,
  linkedin_context: false,
  applied_jobs: [],
  tier: "FREE",
  shared_generation_credits: 0,
  fetch_jobs_credits: 0,
};

const UserContext = createContext<UserContextType>({
  user: defaultUser,
  loading: true,
  isLoggedIn: false,
  refreshUser: async () => {},
  logout: async () => {},
});

export const useUser = () => useContext(UserContext);

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserData>(defaultUser);
  const [loading, setLoading] = useState(true);

  const fetchUserData = useCallback(async () => {
    try {
      const { data: sessionData, error: sessionError } = await supabase.auth.getSession();
      
      if (sessionError || !sessionData?.session?.user) {
        setUser(defaultUser);
        setLoading(false);
        sessionStorage.clear();
        return;
      }

      const authUser = sessionData.session.user;
      const userId = authUser.id;
      const metadata = authUser.user_metadata || {};

      console.log(authUser)
      // Store basic info from auth
      sessionStorage.setItem("id", userId);
      sessionStorage.setItem("email", metadata.email || authUser.email || "");
      sessionStorage.setItem("name", metadata.username || metadata.full_name || metadata.name || "");

      // Fetch additional data from public.User table
      let resumeUrl: string | null = null;
      let profileImage: string | null = metadata.avatar_url || metadata.picture || null;
      let linkedinContext = false;
      let dbName: string | null = null;
      let appliedJobs: string[] = [];
      let tier = "FREE";
      let sharedGenerationCredits = 0;
      let fetchJobsCredits = 0;

      try {
        const res = await fetch(`/api/User?id=${userId}`, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        });
        const userData = await res.json();

        if (userData.user) {
          resumeUrl = userData.user.resume_url || null;
          if (userData.user.profile_image) {
            profileImage = userData.user.profile_image;
          }
          if (userData.user.linkedin_context) {
            linkedinContext = true;
          }
          if (userData.user.name) {
            dbName = userData.user.name;
          }
          if (Array.isArray(userData.user.applied_jobs)) {
            appliedJobs = userData.user.applied_jobs;
          }
          if (userData.user.tier) {
            tier = userData.user.tier;
          }
          if (typeof userData.user.shared_generation_credits === "number") {
            sharedGenerationCredits = userData.user.shared_generation_credits;
          }
          if (typeof userData.user.fetch_jobs_credits === "number") {
            fetchJobsCredits = userData.user.fetch_jobs_credits;
          }
        }
      } catch (err) {
        console.error("Error fetching user data from DB:", err);
      }

      // Update sessionStorage
      if (resumeUrl) {
        sessionStorage.setItem("resume", resumeUrl);
      }
      sessionStorage.setItem("Lcontext", linkedinContext ? "true" : "false");

      const finalName = dbName || metadata.username || metadata.full_name || metadata.name || null;

      setUser({
        id: userId,
        email: metadata.email || authUser.email || null,
        name: finalName,
        resume_url: resumeUrl,
        profile_image: profileImage,
        linkedin_context: linkedinContext,
        applied_jobs: appliedJobs,
        tier: tier,
        shared_generation_credits: sharedGenerationCredits,
        fetch_jobs_credits: fetchJobsCredits,
      });
      setLoading(false);
    } catch (err) {
      console.error("Error in fetchUserData:", err);
      setUser(defaultUser);
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setUser(defaultUser);
    sessionStorage.clear();
    await supabase.auth.signOut();
    window.location.href = "/";
  }, []);

  useEffect(() => {
    fetchUserData();

    // Listen for auth state changes (login/logout)
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (event === "SIGNED_IN" && session?.user) {
        // Sync to public.User table for OAuth users
        const authUser = session.user;
        const metadata = authUser.user_metadata || {};
        const profileImage = metadata.avatar_url || metadata.picture || null;
        const name = metadata.full_name || metadata.name || null;

        try {
          await fetch("/api/User?action=upsert", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              id: authUser.id,
              email: authUser.email,
              name: name,
              profile_image: profileImage,
            }),
          });
        } catch (err) {
          console.error("Failed to sync user:", err);
        }

        fetchUserData();
      } else if (event === "SIGNED_OUT") {
        setUser(defaultUser);
        sessionStorage.clear();
      }
    });

    // Listen for resume upload events
    const handleResumeUploaded = () => fetchUserData();
    window.addEventListener("resume-uploaded", handleResumeUploaded);

    return () => {
      subscription.unsubscribe();
      window.removeEventListener("resume-uploaded", handleResumeUploaded);
    };
  }, [fetchUserData]);

  return (
    <UserContext.Provider
      value={{
        user,
        loading,
        isLoggedIn: !!user.id,
        refreshUser: fetchUserData,
        logout,
      }}
    >
      {children}
    </UserContext.Provider>
  );
}
