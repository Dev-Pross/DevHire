// export default {
//   database: {
//     url: process.env.DATABASE_URL,
//   },
// }


import { defineConfig } from "prisma/config";
import dotenv from "dotenv";

// Explicitly load environment variables from .env if present
dotenv.config();

// Retrieve DATABASE_URL from environment or .env file
const databaseUrl = process.env.DATABASE_URL;

if (!databaseUrl) {
  throw new Error("DATABASE_URL is not defined in environment variables or .env file");
}

export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: {
    path: "prisma/migrations",
  },
  // engine: "classic",
  // Note: 'datasource' is not a valid property for PrismaConfig, so it has been removed.
});