import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { PostgresLearningStore } from '../src/infrastructure/postgres-store.js';
import { PostgresLearningEngine } from '../src/application/postgres-learning-engine.js';

const databaseUrl = process.env.DATABASE_URL;

test('PostgreSQL learning path persists real learner evidence', async (t) => {
  if (!databaseUrl) { t.skip('DATABASE_URL is required for the PostgreSQL integration suite'); return; }
  const pool = createPostgresPool();
  const store = new PostgresLearningStore(pool);
  const nickname = `pg-integration-${process.pid}-${Date.now()}`;
  try {
    const studentId = await store.ensureStudent(nickname);
    const engine = new PostgresLearningEngine(store);
    const initial = await engine.start(studentId);
    assert.equal(initial.studentId, studentId);
    const after = await engine.recordStructuredAttempt(studentId, 'forces', {
      correct: false,
      reasoning: 'The force makes an object move even when the net force is zero.',
      problemId: 'practice-forces-1',
    });
    assert.ok(after.activeMisconceptions.length > 0);
    const intervention = await engine.nextIntervention(studentId);
    assert.ok(intervention);
    const persisted = await store.listInterventions(studentId);
    assert.equal(persisted.length, 1);
    const evidence = await pool.query('SELECT count(*)::int AS count FROM evidence WHERE student_id=$1', [studentId]);
    assert.equal(Number(evidence.rows[0].count), 1);
  } finally {
    await pool.query('DELETE FROM students WHERE nickname=$1', [nickname]);
    await store.close();
  }
});
