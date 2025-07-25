// app/api/user/route.ts
import { NextResponse, NextRequest } from "next/server";
import { getToken } from "next-auth/jwt";
import { PrismaClient } from "@prisma/client";

// Singleton pattern for PrismaClient to avoid hot-reload issues in development
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
  // Try to get the token from the request
  const token = await getToken({
    req,
    secret: process.env.NEXTAUTH_SECRET,
  });

  // Debug logging: show the decoded token and its fields
  console.log("Decoded token:", token);

  // The token may not have an 'id' field, but may have 'sub' (subject) as the user id
  // See your decoded token example:
  // {
  //   name: 'NewOne',
  //   email: 'NewOne@gmail.com',
  //   sub: '12aea842-24da-41fd-8fef-b3dc4e637896',
  //   iat: ...,
  //   exp: ...,
  //   jti: ...
  // }
  // So, use token.sub as the user id

  const userId = token?.id || token?.sub;

  if (!token || !userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const user = await getUserById(String(userId));

  if (!user) {
    return NextResponse.json({ error: "User not found" }, { status: 404 });
  }

  return NextResponse.json(user);
}
