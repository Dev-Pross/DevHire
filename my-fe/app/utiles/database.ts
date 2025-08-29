import { PrismaClient, Prisma } from "@prisma/client"

export const prisma = new PrismaClient()

// Async function to fetch and log users
async function logUsers() {
  const users = await prisma.user.findMany()
  console.log(users)
}

// Call the async function
logUsers()

export async function UserOperations(userData: any) {
  return prisma.user.upsert({
    where: { id: userData.id },
    update: userData,
    create: userData,
  })
}
