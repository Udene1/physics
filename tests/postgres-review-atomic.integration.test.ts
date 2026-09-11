import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { PostgresLearningStore } from '../src/infrastructure/postgres-store.js';

test('PostgreSQL review outcome rolls back every state change on constraint failure', async (t) => {
  if (!process.env.DATABASE_URL) return t.skip('DATABASE_URL is required for PostgreSQL integration tests');
  const pool = createPostgresPool();
  const store = new PostgresLearningStore(pool);
  const nickname = `review-atomic-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const studentId = await store.ensureStudent(nickname);
  try {
    const evidenceId = await store.addEvidence(studentId, 'forces', { kind: 'attempt', value: 0, note: 'seed' });
    const misconception = await store.upsertMisconception(studentId, 'forces', 'force-causes-motion', 3, evidenceId);
    const review = await store.scheduleReview(studentId, 'forces', 1, new Date('2026-01-01T00:00:00Z'));
    const beforeEvidence = await store.query('SELECT COUNT(*)::int AS count FROM evidence WHERE student_id=$1', [studentId]);
    const beforeMastery = await store.query('SELECT attempts,correct,score FROM mastery WHERE student_id=$1 AND concept_id=$2', [studentId, 'forces']);
    const beforeEvents = await store.query('SELECT COUNT(*)::int AS count FROM learning_events WHERE student_id=$1', [studentId]);
    await assert.rejects(store.recordReviewOutcomeAtomic!({ studentId, conceptId: 'forces', problemId: 'force-review-1', evidence: { kind: 'review_attempt', value: 1, note: 'answer', reasoning: 'F=ma' }, outcome: 'retained', checkpointScore: 2, correct: true, misconceptionId: misconception.id, misconceptionVerdict: 'repaired', referenceTime: new Date('2026-01-02T00:00:00Z') }), /review_attempts_checkpoint_score_check/i);
    const afterEvidence = await store.query('SELECT COUNT(*)::int AS count FROM evidence WHERE student_id=$1', [studentId]);
    assert.equal(Number(afterEvidence.rows[0].count), Number(beforeEvidence.rows[0].count));
    const afterMastery = await store.query('SELECT attempts,correct,score FROM mastery WHERE student_id=$1 AND concept_id=$2', [studentId, 'forces']);
    assert.deepEqual(afterMastery.rows, beforeMastery.rows);
    const attempts = await store.query('SELECT COUNT(*)::int AS count FROM review_attempts WHERE student_id=$1', [studentId]);
    assert.equal(Number(attempts.rows[0].count), 0);
    const afterEvents = await store.query('SELECT COUNT(*)::int AS count FROM learning_events WHERE student_id=$1', [studentId]);
    assert.equal(Number(afterEvents.rows[0].count), Number(beforeEvents.rows[0].count));
    const currentReview = (await store.listDueReviews(studentId, '2026-01-03T00:00:00Z')).find(x => x.conceptId === review.conceptId);
    assert.equal(currentReview?.dueAt, review.dueAt);
  } finally {
    await pool.query('DELETE FROM students WHERE id=$1', [studentId]);
    await store.close();
  }
});

test('PostgreSQL successful review commits evidence, mastery, review attempt and ledger events together', async (t) => {
  if (!process.env.DATABASE_URL) return t.skip('DATABASE_URL is required for PostgreSQL integration tests');
  const pool = createPostgresPool();
  const store = new PostgresLearningStore(pool);
  const nickname = `review-commit-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const studentId = await store.ensureStudent(nickname);
  try {
    await store.scheduleReview(studentId, 'forces', 1, new Date('2026-01-01T00:00:00Z'));
    const beforeEvidence = await store.query('SELECT COUNT(*)::int AS count FROM evidence WHERE student_id=$1', [studentId]);
    const beforeEvents = await store.query('SELECT COUNT(*)::int AS count FROM learning_events WHERE student_id=$1', [studentId]);
    const beforeMastery = await store.query('SELECT attempts,correct FROM mastery WHERE student_id=$1 AND concept_id=$2', [studentId, 'forces']);
    const attemptId = await store.recordReviewOutcomeAtomic!({ studentId, conceptId: 'forces', problemId: 'force-review-1', evidence: { kind: 'review_attempt', value: 1, note: 'answer', reasoning: 'F_net = ma; acceleration changes velocity.' }, outcome: 'retained', checkpointScore: 1, correct: true, misconceptionId: null, misconceptionVerdict: 'retained', referenceTime: new Date('2026-01-02T00:00:00Z') });
    assert.ok(attemptId > 0);
    const afterEvidence = await store.query('SELECT COUNT(*)::int AS count FROM evidence WHERE student_id=$1', [studentId]);
    assert.equal(Number(afterEvidence.rows[0].count), Number(beforeEvidence.rows[0].count) + 1);
    const afterMastery = await store.query('SELECT attempts,correct FROM mastery WHERE student_id=$1 AND concept_id=$2', [studentId, 'forces']);
    assert.equal(Number(afterMastery.rows[0].attempts), Number(beforeMastery.rows[0]?.attempts ?? 0) + 1);
    assert.equal(Number(afterMastery.rows[0].correct), Number(beforeMastery.rows[0]?.correct ?? 0) + 1);
    const attempts = await store.query('SELECT id,outcome,checkpoint_score FROM review_attempts WHERE id=$1', [attemptId]);
    assert.deepEqual(attempts.rows.map(row => ({ id: Number(row.id), outcome: String(row.outcome), checkpoint: Number(row.checkpoint_score) })), [{ id: attemptId, outcome: 'retained', checkpoint: 1 }]);
    const events = await store.query("SELECT event_type,aggregate_type,aggregate_id FROM learning_events WHERE student_id=$1 ORDER BY id DESC LIMIT 2", [studentId]);
    assert.equal(events.rows.length, 2);
    assert.deepEqual(events.rows.map(row => String(row.event_type)).sort(), ['evidence.recorded', 'review.attempted'].sort());
    assert.ok(events.rows.some(row => String(row.aggregate_type) === 'review_attempt' && String(row.aggregate_id) === String(attemptId)));
  } finally {
    await pool.query('DELETE FROM students WHERE id=$1', [studentId]);
    await store.close();
  }
});
