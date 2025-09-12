import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

/**
 * Upserts a user record.
 * This is just an example helper — you can add more operations here.
 */
export async function UserOperations(user: {
  id: string;
  email: string;
  name: string;
  resume_url: string | null;
  applied_jobs: any[];
}) {
  return prisma.user.upsert({
    where: { id: user.id },
    update: user,
    create: user,
  });
}

export default prisma; // so other files can still do prisma.user.findMany()
