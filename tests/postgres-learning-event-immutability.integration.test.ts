import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { PostgresLearningStore } from '../src/infrastructure/postgres-store.js';

test('PostgreSQL learning events cannot be updated or deleted', async (t) => {
  if (!process.env.DATABASE_URL) return t.skip('DATABASE_URL is required for PostgreSQL integration tests');
  const pool = createPostgresPool();
  const store = new PostgresLearningStore(pool);
  const nickname = `event-immutable-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const studentId = await store.ensureStudent(nickname);
  try {
    const evidenceId = await store.addEvidence(studentId, 'forces', {
      kind: 'attempt', value: 1, note: 'immutable-ledger-test', problemId: 'force-motion-transfer-1',
    });
    const event = await store.query(
      `SELECT id, event_type, aggregate_type, aggregate_id, concept_id, payload
         FROM learning_events
        WHERE student_id=$1 AND aggregate_type='evidence' AND aggregate_id=$2
        ORDER BY id DESC LIMIT 1`,
      [studentId, String(evidenceId)],
    );
    assert.equal(event.rows.length, 1);
    const eventId = Number(event.rows[0].id);

    await assert.rejects(
      pool.query(`UPDATE learning_events SET payload='{"tampered":true}'::jsonb WHERE id=$1`, [eventId]),
      /learning_events is append-only/i,
    );
    await assert.rejects(
      pool.query('DELETE FROM learning_events WHERE id=$1', [eventId]),
      /learning_events is append-only/i,
    );

    const unchanged = await store.query(
      'SELECT event_type, aggregate_type, aggregate_id, concept_id, payload FROM learning_events WHERE id=$1',
      [eventId],
    );
    assert.equal(unchanged.rows.length, 1);
    assert.equal(unchanged.rows[0].event_type, 'evidence.recorded');
    assert.equal(unchanged.rows[0].aggregate_id, String(evidenceId));
    assert.deepEqual(unchanged.rows[0].payload, {
      kind: 'attempt', problemId: 'force-motion-transfer-1', lessonId: null,
      value: 1, confidence: null, hintUsed: false,
    });
  } finally {
    await pool.query('DELETE FROM students WHERE id=$1', [studentId]);
    await store.close();
  }
});
