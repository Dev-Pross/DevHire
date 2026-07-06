import { Pool } from "pg";
import { config } from "dotenv";

config({ path: '../.env' })

const DBURL = process.env.DATABASE_URL

if (!DBURL) throw new Error('Database URL not found')

export const db = new Pool({
    connectionString: DBURL,
    max: 5
})