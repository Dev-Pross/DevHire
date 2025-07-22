import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

export const authoptions = {
    secret: process.env.NEXTAUTH_SECRET,
    providers: [
      CredentialsProvider({
        name: "Email",
        credentials: {
          email: { label: "Email", type: "text" },
          password: { label: "Password", type: "password" },
        },
        async authorize(credentials) {
          // const { email, password } = credentials ?? {};
          const email = credentials?.email;
          const password = credentials?.password;
          console.log(email,password)
          if (email === "123" || password === "123") {
            return {
              name: "Welcome to this align world",
              id: "1",
            };
          }
          return null;
        },
      }),
    ],
  };
const hadnler = NextAuth(authoptions)

export {hadnler as GET ,  hadnler as POST}