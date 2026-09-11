import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { runMigrations } from '../src/infrastructure/migrate.js';

const url = process.env.DATABASE_URL;

test('PostgreSQL scheduled review cannot be consumed twice concurrently', async (t) => {
  if (!url) {
    t.skip('DATABASE_URL is required for PostgreSQL integration tests');
    return;
  }

  const pool = createPostgresPool();
  await runMigrations(pool);
  const nickname = `review-race-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const clients = [await pool.connect(), await pool.connect()];

  try {
    const student = await pool.query('INSERT INTO students(nickname) VALUES($1) RETURNING id', [nickname]);
    const studentId = Number(student.rows[0].id);
    await pool.query(
      `INSERT INTO concept_reviews(student_id,concept_id,due_at,interval_days,streak,last_score)
       VALUES($1,'forces',now() - interval '1 minute',1,0,0)`,
      [studentId],
    );

    const evidence = await Promise.all([
      pool.query(
        `INSERT INTO evidence(student_id,concept_id,kind,value,problem_id)
         VALUES($1,'forces','review_attempt',1,'review-forces-1') RETURNING id`,
        [studentId],
      ),
      pool.query(
        `INSERT INTO evidence(student_id,concept_id,kind,value,problem_id)
         VALUES($1,'forces','review_attempt',1,'review-forces-1') RETURNING id`,
        [studentId],
      ),
    ]);

    const attempt = async (client: typeof clients[number], evidenceId: number) => {
      await client.query('BEGIN');
      try {
        await client.query(
          `INSERT INTO review_attempts(student_id,concept_id,problem_id,evidence_id,outcome,checkpoint_score)
           VALUES($1,'forces','review-forces-1',$2,'retained',1)`,
          [studentId, evidenceId],
        );
        await client.query(
          `UPDATE concept_reviews
              SET due_at=now() + interval '1 day', interval_days=1, streak=1, last_score=1, updated_at=now()
            WHERE student_id=$1 AND concept_id='forces'`,
          [studentId],
        );
        await client.query('COMMIT');
        return 'committed' as const;
      } catch (error) {
        await client.query('ROLLBACK');
        return error;
      }
    };

    const results = await Promise.all([
      attempt(clients[0], Number(evidence[0].rows[0].id)),
      attempt(clients[1], Number(evidence[1].rows[0].id)),
    ]);

    const committed = results.filter((result) => result === 'committed');
    const rejected = results.filter((result) => result instanceof Error);
    assert.equal(committed.length, 1);
    assert.equal(rejected.length, 1);
    assert.match(String((rejected[0] as Error).message), /no longer due|another attempt/i);

    const attempts = await pool.query(
      `SELECT count(*)::int AS count FROM review_attempts WHERE student_id=$1 AND concept_id='forces'`,
      [studentId],
    );
    assert.equal(Number(attempts.rows[0].count), 1);
  } finally {
    for (const client of clients) client.release();
    const student = await pool.query('SELECT id FROM students WHERE nickname=$1', [nickname]);
    if (student.rowCount === 1) {
      await pool.query('DELETE FROM students WHERE id=$1', [Number(student.rows[0].id)]);
    }
    await pool.end();
  }
});
