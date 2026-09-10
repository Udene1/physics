import { readFile } from 'node:fs/promises';
import { createPostgresPool } from './postgres.js';

const pool = createPostgresPool();

try {
  const sql = await readFile(new URL('../../migrations/001_vita_core.sql', import.meta.url), 'utf8');
  await pool.query(sql);
  console.log('Vita PostgreSQL schema is current.');
} finally {
  await pool.end();
}
