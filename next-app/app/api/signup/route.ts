import { PrismaClient } from "@prisma/client";
import { hash } from "bcrypt";

// ---
// FIX FOR: "prepared statement 's0' already exists"
// This error is common in development with Next.js (especially with hot reload)
// because a new PrismaClient is created on every reload/request, causing connection issues.
// The recommended fix is to use a global singleton for PrismaClient in development.
// ---
// Use a global singleton for PrismaClient to avoid "prepared statement already exists" errors in development.
// This ensures only one PrismaClient instance is used during hot reloads.
if (process.env.NODE_ENV !== "production") {
  if (!globalThis._prisma) {
    globalThis._prisma = new PrismaClient({
      log: ["query", "error", "warn"],
    });
  }
}

// PrismaClient singleton pattern for Next.js (Edge/Serverless safe)
let prisma: PrismaClient;

declare global {
  // eslint-disable-next-line no-var
  var _prisma: PrismaClient | undefined;
}

if (process.env.NODE_ENV === "production") {
  prisma = new PrismaClient({
    log: ["error", "warn"], // Only log errors and warnings in production
  });
} else {
  if (!global._prisma) {
    global._prisma = new PrismaClient({
      log: ["query", "error", "warn"], // Log queries in development for debugging
    });
  }
  prisma = global._prisma;
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { username, email, password } = body;

    // Validate required fields
    if (
      typeof username !== "string" ||
      typeof email !== "string" ||
      typeof password !== "string" ||
      !username.trim() ||
      !email.trim() ||
      !password.trim()
    ) {
      return new Response(
        JSON.stringify({ message: "Missing required fields" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    // Check if user already exists
    const existingUser = await prisma.users.findUnique({
      where: { email },
      select: { id: true },
    });

    if (existingUser) {
      return new Response(
        JSON.stringify({ message: "Email already exists" }),
        { status: 409, headers: { "Content-Type": "application/json" } }
      );
    }

    // Hash the password
    const hashedPassword = await hash(password, 10);

    // Create the user
    const user = await prisma.users.create({
      data: {
        email,
        name: username,
        password: hashedPassword,
      },
      select: { id: true, name: true, email: true },
    });

    return new Response(
      JSON.stringify({
        message: "Signup successful",
        username: user.name,
      }),
      {
        status: 201,
        headers: { "Content-Type": "application/json" },
      }
    );
  } catch (err) {
    console.error("Signup error:", err);
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
