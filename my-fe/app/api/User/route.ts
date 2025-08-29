import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export async function POST(req: Request) {
  const { email, name } = await req.json();
  const users = await prisma.user.create({
    data: {
      email: email,
      name: name,
    },
  });
  console.log(users);
  return new Response(JSON.stringify(users), {
    headers: { "Content-Type": "application/json" },
  });
}

export { POST as default };
