import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL, // use your actual URL or env var
});
if (pool) {
    console.log("Db Connectioni sucesfull");
  } else {
    console.log("connection failed");
  }

export default pool;
