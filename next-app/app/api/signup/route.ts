import { PrismaClient } from "@prisma/client";
import { hash } from "bcrypt";

const prisma = new PrismaClient();

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

    // Check if user with this email already exists
    const existingUser = await prisma.users.findUnique({
      where: { email: email },
      // Only select the id to avoid Prisma error if password is null
      select: { id: true },
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
