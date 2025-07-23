import { PrismaClient } from "@prisma/client";
// import { PrismaClient } from "@prisma/client";
export async function POST(req: Request) {
  try {
    const prisma = new PrismaClient();

    const { username, email, password } = await req.json();
    const result = await prisma.$queryRaw`SELECT NOW() as currentDate`;
    console.log(result);
    const user = await prisma.users.create({
      data: {
        // If prisma migrate is too slow, you can use SQL directly to insert the user as a workaround.
        // Example using $executeRaw (not recommended for production without validation!):
        // await prisma.$executeRaw`INSERT INTO users (email, id) VALUES (${email}, ${password})`;

        // Or, if you want to use the Prisma client and skip migrations, ensure your table exists in the DB.
        // You can also use a tool like `psql` or a GUI to manually create the table/schema.

        // For now, using Prisma client as before, but ensure your DB schema is ready:
        email: email,
        // id: password, // Don't use password as id! Use a proper UUID or let DB auto-generate.
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
