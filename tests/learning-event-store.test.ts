import test from 'node:test';
import assert from 'node:assert/strict';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { PostgresLearningStore } from '../src/infrastructure/postgres-store.js';
import { LearningEventStore } from '../src/infrastructure/learning-event-store.js';

test('PostgreSQL learning event ledger appends and reads immutable learner events', async () => {
  const pool = createPostgresPool();
  const store = new PostgresLearningStore(pool);
  const events = new LearningEventStore(pool);
  const nickname = `event-test-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  try {
    const studentId = await store.ensureStudent(nickname);
    const eventId = await events.append({
      studentId,
      eventType: 'practice.submitted',
      aggregateType: 'practice_attempt',
      aggregateId: 'forces-1',
      conceptId: 'forces',
      payload: { correct: false, checkpointScore: 0.25 },
    });
    assert.ok(eventId > 0);

    const listed = await events.list(studentId);
    assert.equal(listed.length, 1);
    assert.equal(listed[0].id, eventId);
    assert.equal(listed[0].eventType, 'practice.submitted');
    assert.equal(listed[0].aggregateId, 'forces-1');
    assert.equal(listed[0].conceptId, 'forces');
    assert.deepEqual(listed[0].payload, { correct: false, checkpointScore: 0.25 });
  } finally {
    await pool.query('DELETE FROM students WHERE nickname = $1', [nickname]);
    await store.close();
  }
});
