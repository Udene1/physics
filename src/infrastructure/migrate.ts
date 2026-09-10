import { readFile } from 'node:fs/promises';
import { createPostgresPool } from './postgres.js';
const pool=createPostgresPool();
try{
  const client=await pool.connect();
  try{
    await client.query('BEGIN');
    await client.query('SELECT pg_advisory_xact_lock($1)',[73291401]);
    const sql=await readFile(new URL('../../migrations/001_vita_core.sql',import.meta.url),'utf8');
    await client.query(sql);
    const result=await client.query("SELECT version FROM schema_migrations ORDER BY version");
    if(!result.rows.some(r=>r.version==='001_vita_core'))throw new Error('Migration 001_vita_core did not register');
    await client.query('COMMIT');
    console.log(`Vita PostgreSQL schema is current (${result.rows.length} migration(s)).`);
  }catch(error){await client.query('ROLLBACK');throw error;}finally{client.release();}
}finally{await pool.end();}
