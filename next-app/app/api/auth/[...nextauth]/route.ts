import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import EmailProvider from "next-auth/providers/email";
import { NextResponse } from "next/server";

const authoptions = {
  secret: process.env.NEXTAUTH_SECRET,
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: {
          label: "Email",
          type: "email",
          placeholder: "Enter your email",
        },
        username: {
          label: "Username",
          type: "text",
          placeholder: "Enter your username",
        },
        password: {
          label: "Password",
          type: "password",
          placeholder: "Enter your password",
        },
      },
      async authorize(credentials, req) {
        const username1 = credentials?.username;
        const password1 = credentials?.password;

        const user = {
          name: "Hello world ",
          username: "kingu",
          id: "34",
        }
        if (username1 == "123" || password1 == "123") {
          return user;
        }
        // Implement your own logic here to find the user and validate credentials
        // Example:
        // if (credentials?.username === "admin" && credentials?.password === "admin") {
        //   return { id: 1, name: "Admin", email: "admin@example.com" };
        // }
        // return null;
        return null;
      },
    }),
    // You can add EmailProvider or other providers here if needed
    // EmailProvider({
    //   server: process.env.EMAIL_SERVER,
    //   from: process.env.EMAIL_FROM,
    // }),
  ],
};

const handler = NextAuth(authoptions);

export { handler as POST, handler as GET };
