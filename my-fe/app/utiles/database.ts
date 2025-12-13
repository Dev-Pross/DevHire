import { PrismaClient } from '@prisma/client';
import { PrismaPg } from '@prisma/adapter-pg';
import { Pool } from 'pg';

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

function createPrismaClient() {
  const connectionString = process.env.DATABASE_URL;
  if (!connectionString) {
    throw new Error('DATABASE_URL environment variable is not set');
  }

  const pool = new Pool({ connectionString });
  const adapter = new PrismaPg(pool);
  return new PrismaClient({ adapter });
}

const prisma = globalForPrisma.prisma ?? createPrismaClient();

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma;

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
