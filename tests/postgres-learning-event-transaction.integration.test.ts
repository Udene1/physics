import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { runMigrations } from '../src/infrastructure/migrate.js';

const url = process.env.DATABASE_URL;

test('PostgreSQL learning event triggers commit with domain writes', async (t) => {
  if (!url) {
    t.skip('DATABASE_URL is required for PostgreSQL integration tests');
    return;
  }

  const pool = createPostgresPool();
  await runMigrations(pool);
  const nickname = `event-transaction-${Date.now()}-${Math.random().toString(36).slice(2)}`;

  try {
    const student = await pool.query(
      'INSERT INTO students(nickname) VALUES($1) RETURNING id',
      [nickname],
    );
    const studentId = Number(student.rows[0].id);

    const evidence = await pool.query(
      `INSERT INTO evidence(student_id,concept_id,kind,value,problem_id)
       VALUES($1,'forces','attempt',1,'force-problem-1') RETURNING id`,
      [studentId],
    );
    const evidenceId = Number(evidence.rows[0].id);

    const intervention = await pool.query(
      `INSERT INTO misconceptions(student_id,concept_id,code,severity)
       VALUES($1,'forces','force-motion',2) RETURNING id`,
      [studentId],
    );
    const misconceptionId = Number(intervention.rows[0].id);
    const queued = await pool.query(
      `INSERT INTO interventions(student_id,misconception_id,concept_id,prerequisite_concept_id,problem_id,stage,strategy)
       VALUES($1,$2,'forces','motion','force-motion-discrimination-1','discrimination','separate force from motion') RETURNING id`,
      [studentId, misconceptionId],
    );
    const interventionId = Number(queued.rows[0].id);

    const before = await pool.query(
      'SELECT count(*)::int AS count FROM learning_events WHERE student_id=$1',
      [studentId],
    );
    assert.equal(Number(before.rows[0].count), 1);

    await pool.query(
      `INSERT INTO remediation_attempts(intervention_id,evidence_id,verdict,checkpoint_score)
       VALUES($1,$2,'still_present',0.25)`,
      [interventionId, evidenceId],
    );

    const after = await pool.query(
      `SELECT event_type, aggregate_type, payload
       FROM learning_events WHERE student_id=$1 ORDER BY id`,
      [studentId],
    );
    assert.equal(after.rows.length, 2);
    assert.equal(after.rows[0].event_type, 'evidence.recorded');
    assert.equal(after.rows[1].event_type, 'remediation.attempted');
    assert.equal(after.rows[1].aggregate_type, 'remediation_attempt');
    assert.equal(after.rows[1].payload.verdict, 'still_present');

    await pool.query('DELETE FROM students WHERE id=$1', [studentId]);
  } finally {
    await pool.end();
  }
});

test('learning event trigger rolls back with its transaction', async (t) => {
  if (!url) {
    t.skip('DATABASE_URL is required for PostgreSQL integration tests');
    return;
  }

  const pool = createPostgresPool();
  await runMigrations(pool);
  const nickname = `event-rollback-${Date.now()}-${Math.random().toString(36).slice(2)}`;

  try {
    const student = await pool.query(
      'INSERT INTO students(nickname) VALUES($1) RETURNING id',
      [nickname],
    );
    const studentId = Number(student.rows[0].id);

    await assert.rejects(
      pool.query('BEGIN').then(async () => {
        await pool.query(
          `INSERT INTO evidence(student_id,concept_id,kind,value)
           VALUES($1,'forces','attempt',0)`,
          [studentId],
        );
        throw new Error('forced rollback');
      }),
    ).catch(() => undefined);
    await pool.query('ROLLBACK').catch(() => undefined);

    const events = await pool.query(
      'SELECT count(*)::int AS count FROM learning_events WHERE student_id=$1',
      [studentId],
    );
    assert.equal(Number(events.rows[0].count), 0);
    await pool.query('DELETE FROM students WHERE id=$1', [studentId]);
  } finally {
    await pool.end();
  }
});
