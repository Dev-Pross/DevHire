import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { PrismaClient } from "@prisma/client";
import { compare } from "bcrypt";

// How to send error details to the frontend with NextAuth credentials provider?
// - You cannot return a custom Response from `authorize`.
// - Instead, throw an Error with a message. NextAuth will redirect to the sign-in page with an error query param.
// - On the frontend, you can read the error param and show a custom message.
// - You can also use `callbacks` to customize error handling further.

const prisma = new PrismaClient();

export const authoptions = {
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
        password: {
          label: "Password",
          type: "password",
          placeholder: "Enter your password",
        },
      },
      async authorize(credentials) {
        const email = credentials?.email;
        const password = credentials?.password;

        if (!email || !password) {
          // Missing required fields
          throw new Error("Missing email or password");
        }

        // Find user by email
        const user = await prisma.users.findUnique({
          where: { email },
        });

        if (!user || !user.password) {
          // User not found or no password set
          throw new Error("No user found with this email");
        }

        // Compare password
        const isMatch = await compare(password, user.password);
        if (!isMatch) {
          // Invalid password
          throw new Error("Invalid password");
        }

        return {
          id: user.id,
          name: user.name,
          email: user.email,
        };
      },
    }),
    // Add other providers here if needed
  ],
};

const handler = NextAuth(authoptions);

export { handler as POST, handler as GET };
