import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { runMigrations } from '../src/infrastructure/migrate.js';

const url = process.env.DATABASE_URL;

test('PostgreSQL learning state transitions append immutable domain events', async (t) => {
  if (!url) {
    t.skip('DATABASE_URL is required for PostgreSQL integration tests');
    return;
  }

  const pool = createPostgresPool();
  await runMigrations(pool);
  const nickname = `state-events-${Date.now()}-${Math.random().toString(36).slice(2)}`;

  try {
    const student = await pool.query('INSERT INTO students(nickname) VALUES($1) RETURNING id', [nickname]);
    const studentId = Number(student.rows[0].id);
    const evidence = await pool.query(
      `INSERT INTO evidence(student_id,concept_id,kind,value,problem_id)
       VALUES($1,'forces','attempt',0,'force-problem-1') RETURNING id`,
      [studentId],
    );
    const misconception = await pool.query(
      `INSERT INTO misconceptions(student_id,concept_id,code,severity,last_evidence_id)
       VALUES($1,'forces','force-motion',2,$2) RETURNING id`,
      [studentId, Number(evidence.rows[0].id)],
    );
    const misconceptionId = Number(misconception.rows[0].id);
    const intervention = await pool.query(
      `INSERT INTO interventions(student_id,misconception_id,concept_id,prerequisite_concept_id,problem_id,stage,strategy)
       VALUES($1,$2,'forces','motion','force-motion-discrimination-1','discrimination','separate force from motion') RETURNING id`,
      [studentId, misconceptionId],
    );
    const interventionId = Number(intervention.rows[0].id);

    await pool.query("UPDATE misconceptions SET status='resolved' WHERE id=$1", [misconceptionId]);
    await pool.query("UPDATE interventions SET status='active' WHERE id=$1", [interventionId]);

    const events = await pool.query(
      `SELECT event_type, aggregate_type, aggregate_id, payload
         FROM learning_events
        WHERE student_id=$1
        ORDER BY id`,
      [studentId],
    );
    const types = events.rows.map((row) => row.event_type);
    assert.ok(types.includes('evidence.recorded'));
    assert.ok(types.includes('misconception.state_changed'));
    assert.ok(types.includes('intervention.state_changed'));

    const misconceptionEvent = events.rows.find((row) => row.event_type === 'misconception.state_changed');
    assert.equal(misconceptionEvent.aggregate_type, 'misconception');
    assert.equal(misconceptionEvent.payload.previousStatus, 'active');
    assert.equal(misconceptionEvent.payload.status, 'resolved');

    const interventionEvent = events.rows.find((row) => row.event_type === 'intervention.state_changed');
    assert.equal(interventionEvent.aggregate_type, 'intervention');
    assert.equal(interventionEvent.payload.previousStatus, 'queued');
    assert.equal(interventionEvent.payload.status, 'active');
  } finally {
    const student = await pool.query('SELECT id FROM students WHERE nickname=$1', [nickname]);
    if (student.rowCount === 1) await pool.query('DELETE FROM students WHERE id=$1', [Number(student.rows[0].id)]);
    await pool.end();
  }
});
