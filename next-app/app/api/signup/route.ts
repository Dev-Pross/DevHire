
import { PrismaClient } from "@prisma/client";
// import { PrismaClient } from "@prisma/client";
export async function POST(req: Request) {
    
  try {
    const prisma = new PrismaClient();

    const { username, email, password } = await req.json();
    const user = await prisma.users.create({
      data: {
        full_name: username,
        email: email,
        id: password,
      },
    });
    console.log(username, password);
    console.log(user);

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
