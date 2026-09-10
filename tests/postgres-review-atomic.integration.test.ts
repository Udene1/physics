import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { PostgresLearningStore } from '../src/infrastructure/postgres-store.js';

test('PostgreSQL review outcome rolls back every state change on failure', async (t) => {
  if (!process.env.DATABASE_URL) return t.skip('DATABASE_URL is required for PostgreSQL integration tests');
  const pool = createPostgresPool();
  const store = new PostgresLearningStore(pool);
  const nickname = `review-atomic-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const studentId = await store.ensureStudent(nickname);
  try {
    const evidenceId = await store.addEvidence(studentId, 'forces', { kind: 'attempt', value: 0, note: 'seed' });
    const misconception = await store.upsertMisconception(studentId, 'forces', 'force-causes-motion', 3, evidenceId);
    const review = await store.scheduleReview(studentId, 'forces', 1, new Date('2026-01-01T00:00:00Z'));
    const before = await store.query('SELECT COUNT(*)::int AS count FROM evidence WHERE student_id=$1', [studentId]);
    await assert.rejects(
      store.recordReviewOutcomeAtomic!({
        studentId, conceptId: 'forces', problemId: 'force-review-1',
        evidence: { kind: 'review_attempt', value: 1, note: 'answer', reasoning: 'F=ma' },
        outcome: 'retained', checkpointScore: 1, correct: true,
        misconceptionId: misconception.id, misconceptionVerdict: 'repaired',
        referenceTime: new Date('2026-01-02T00:00:00Z'),
      }),
      /relation .*does_not_exist|undefined/i,
    );
    const after = await store.query('SELECT COUNT(*)::int AS count FROM evidence WHERE student_id=$1', [studentId]);
    assert.equal(Number(after.rows[0].count), Number(before.rows[0].count));
    const attempts = await store.query('SELECT COUNT(*)::int AS count FROM review_attempts WHERE student_id=$1', [studentId]);
    assert.equal(Number(attempts.rows[0].count), 0);
    const currentReview = (await store.listDueReviews(studentId, '2026-01-03T00:00:00Z')).find(x => x.conceptId === review.conceptId);
    assert.equal(currentReview?.dueAt, review.dueAt);
  } finally {
    await pool.query('DELETE FROM students WHERE id=$1', [studentId]);
    await store.close();
  }
});
