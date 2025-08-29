import { PrismaClient } from "@prisma/client";

export const prisma = new PrismaClient();

// Async function to fetch and log users
async function logUsers() {
  const users = await prisma.user.findMany();
  console.log(users);
}

// Call the async function
logUsers();

export async function UserOperations() {
  // Create a new user
  
  const newUser = await prisma.user.create({
    data: {
      email: " HelloWOrld@gmail.com"
    }
  });
  console.log("Created new user:", newUser);
 
}
