import pg from 'pg';

const { Pool } = pg;

export interface PostgresConfig {
  connectionString: string;
  maxConnections: number;
  statementTimeoutMs: number;
  idleTimeoutMs: number;
  ssl: boolean;
}

export function postgresConfig(env: NodeJS.ProcessEnv = process.env): PostgresConfig {
  const connectionString = env.DATABASE_URL?.trim();
  if (!connectionString) throw new Error('DATABASE_URL is required; Vita no longer has an implicit local database');
  return {
    connectionString,
    maxConnections: positiveInt(env.PG_POOL_MAX, 10),
    statementTimeoutMs: positiveInt(env.PG_STATEMENT_TIMEOUT_MS, 10000),
    idleTimeoutMs: positiveInt(env.PG_IDLE_TIMEOUT_MS, 30000),
    ssl: env.PGSSL === 'true' || env.NODE_ENV === 'production',
  };
}

function positiveInt(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

export function createPostgresPool(config = postgresConfig()): pg.Pool {
  return new Pool({
    connectionString: config.connectionString,
    max: config.maxConnections,
    idleTimeoutMillis: config.idleTimeoutMs,
    statement_timeout: config.statementTimeoutMs,
    ssl: config.ssl ? { rejectUnauthorized: false } : undefined,
    application_name: 'vita-learning-engine',
  });
}

export async function assertPostgresReady(pool: pg.Pool): Promise<void> {
  const client = await pool.connect();
  try {
    await client.query('SELECT 1');
  } finally {
    client.release();
  }
}

export async function closePostgres(pool: pg.Pool): Promise<void> {
  await pool.end();
}
