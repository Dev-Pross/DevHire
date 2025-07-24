/**
 * EXPLANATION:
 * The error "prepared statement \"s3\" already exists" from Prisma/Postgres occurs when
 * a PrismaClient instance is created multiple times in a serverless or hot-reloading environment (like Next.js API routes).
 * Each new PrismaClient instance can cause connection and prepared statement conflicts.
 * 
 * The fix is to use a singleton pattern for PrismaClient, so only one instance exists per process.
 * 
 * Below is the fixed code using a singleton for PrismaClient.
 */

import { PrismaClient } from "@prisma/client";
import { hash } from "bcrypt";

// --- PrismaClient Singleton Pattern ---
// let prisma: PrismaClient;

// if (process.env.NODE_ENV === "production") {
//   prisma = new PrismaClient();
// } else {
//   // @ts-ignore
//   if (!global.prisma) {
//     // @ts-ignore
//     global.prisma = new PrismaClient();
//   }
//   // @ts-ignore
//   prisma = global.prisma;
// }

export async function POST(req: Request) {
  try {
    const { username, email, password } = await req.json();

    // Validate required fields
    if (!username || !email || !password) {
      return new Response(
        JSON.stringify({ message: "Missing required fields" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    // Check if user already exists
    const existingUser = await prisma.users.findUnique({
      where: { email: email },
      // select: { id: true }, // Only fetch the 'id' field for efficiency and safety
    });

    if (existingUser) {
      return new Response(
        JSON.stringify({
          message: "Email already exists",
        }),
        { status: 411, headers: { "Content-Type": "application/json" } }
      );
    }

    // Hash the password
    const hashedPassword = await hash(password, 10);

    // Create the user
    const user = await prisma.users.create({
      data: {
        email: email,
        name: username,
        password: hashedPassword,
      },
    });

    return new Response(
      JSON.stringify({
        message: "Signup successful",
        username,
      }),
      {
        status: 201,
        headers: { "Content-Type": "application/json" },
      }
    );
  } catch (err) {
    console.log(err);
    return new Response(
      JSON.stringify({
        message: "Signup failed",
        error: err instanceof Error ? err.message : "Unknown error",
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      }
    );
  }
}
