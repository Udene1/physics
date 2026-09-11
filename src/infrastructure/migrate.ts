import { readdir, readFile } from 'node:fs/promises';
import type { Pool, PoolClient } from 'pg';
import { createPostgresPool } from './postgres.js';

const MIGRATION_LOCK = 73291401;

export async function runMigrations(pool: Pool): Promise<void> {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    await client.query('SELECT pg_advisory_xact_lock($1)', [MIGRATION_LOCK]);
    await client.query(
      'CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())',
    );

    const directory = new URL('../../migrations/', import.meta.url);
    const files = (await readdir(directory))
      .filter((name) => /^\d+_[a-z0-9_-]+\.sql$/i.test(name))
      .sort();

    for (const name of files) {
      const version = name.replace(/\.sql$/i, '');
      const existing = await client.query(
        'SELECT 1 FROM schema_migrations WHERE version=$1',
        [version],
      );
      if (existing.rowCount) continue;

      const sql = await readFile(new URL(name, directory), 'utf8');
      await client.query(sql);
      const registered = await client.query(
        'SELECT 1 FROM schema_migrations WHERE version=$1',
        [version],
      );
      if (!registered.rowCount) {
        await client.query('INSERT INTO schema_migrations(version) VALUES($1)', [version]);
      }
    }

    await client.query('COMMIT');
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}

export async function migrateAndClose(pool: Pool): Promise<void> {
  try {
    await runMigrations(pool);
    const result = await pool.query('SELECT version FROM schema_migrations ORDER BY version');
    console.log(`Vita PostgreSQL schema is current (${result.rows.length} migration(s)).`);
  } finally {
    await pool.end();
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await migrateAndClose(createPostgresPool());
}
