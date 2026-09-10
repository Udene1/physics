import { readdir, readFile } from 'node:fs/promises';
import { createPostgresPool } from './postgres.js';

const pool=createPostgresPool();
try{
  const client=await pool.connect();
  try{
    await client.query('BEGIN');
    await client.query('SELECT pg_advisory_xact_lock($1)',[73291401]);
    await client.query('CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())');
    const directory=new URL('../../migrations/',import.meta.url);
    const files=(await readdir(directory)).filter((name)=>/^\d+_[a-z0-9_-]+\.sql$/i.test(name)).sort();
    for(const name of files){
      const version=name.replace(/\.sql$/i,'');
      const existing=await client.query('SELECT 1 FROM schema_migrations WHERE version=$1',[version]);
      if(existing.rowCount)continue;
      const sql=await readFile(new URL(name,directory),'utf8');
      await client.query(sql);
      const registered=await client.query('SELECT 1 FROM schema_migrations WHERE version=$1',[version]);
      if(!registered.rowCount)await client.query('INSERT INTO schema_migrations(version) VALUES($1)',[version]);
    }
    const result=await client.query('SELECT version FROM schema_migrations ORDER BY version');
    await client.query('COMMIT');
    console.log(`Vita PostgreSQL schema is current (${result.rows.length} migration(s)).`);
  }catch(error){await client.query('ROLLBACK');throw error;}finally{client.release();}
}finally{await pool.end();}
