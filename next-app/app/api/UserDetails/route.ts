// app/api/UserDetails/route.ts
import { NextResponse, NextRequest } from "next/server";
import { PrismaClient } from "@prisma/client";
import { getToken } from "next-auth/jwt";

// --- PrismaClient singleton pattern (same as in signup route) ---
let prisma: PrismaClient;
declare global {
  // eslint-disable-next-line no-var
  var _prisma: PrismaClient | undefined;
}

if (process.env.NODE_ENV === "production") {
  prisma = new PrismaClient();
} else {
  if (!global._prisma) {
    global._prisma = new PrismaClient();
  }
  prisma = global._prisma;
}

// Helper function to fetch user by ID
async function getUserById(userId: string) {
  try {
    const user = await prisma.users.findUnique({
      where: { id: userId },
      select: {
        id: true,
        name: true,
        email: true,
      },
    });
    return user;
  } catch (error) {
    console.error("Error fetching user:", error);
    return null;
  }
}

// Main handler for GET request
export async function GET(req: NextRequest) {
  // --- Apply the same logic as the middleware for authentication ---
  // (middleware.ts uses getToken to check for a valid session token)
  const token = await getToken({
    req,
    secret: process.env.NEXTAUTH_SECRET,
  });

  if (!token) {
    // Not authenticated, redirect to /signin (same as middleware)
    return NextResponse.redirect(new URL("/signin", req.url));
  }

  // Extract user id from token (id or sub)
  const userId = token.id || token.sub;
  // if (!userId) {
  //   return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  // }

  const user = await getUserById(String(userId));
  if (!user) {
    return NextResponse.json({ error: "User not found" }, { status: 404 });
  }

  return NextResponse.json(user);
}
