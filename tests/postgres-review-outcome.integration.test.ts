import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { PostgresLearningStore } from '../src/infrastructure/postgres-store.js';

test('PostgreSQL review outcome commits evidence, mastery, misconception state, review attempt and schedule together', async (t) => {
  if (!process.env.DATABASE_URL) return t.skip('DATABASE_URL is required for PostgreSQL integration tests');
  const pool = createPostgresPool();
  const store = new PostgresLearningStore(pool);
  const nickname = `review-atomic-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const studentId = await store.ensureStudent(nickname);
  try {
    const seedEvidenceId = await store.addEvidence(studentId, 'forces', { kind: 'attempt', value: 0, note: 'initial diagnostic evidence' });
    const misconception = await store.upsertMisconception(studentId, 'forces', 'force_causes_motion', 2, seedEvidenceId);
    await store.recordMisconceptionSignal(misconception.id, 'still_present');
    await store.scheduleReview(studentId, 'forces', 0, new Date('2026-01-01T00:00:00Z'));

    const attemptId = await store.recordReviewOutcomeAtomic({
      studentId,
      conceptId: 'forces',
      problemId: 'force-motion-transfer-1',
      evidence: {
        kind: 'review_attempt',
        value: 1,
        note: 'F_net = ma; the force changes velocity through acceleration.',
        problemId: 'force-motion-transfer-1',
        reasoning: 'Net force causes acceleration, and acceleration changes velocity.',
        confidence: 0.9,
        hintUsed: false,
      },
      outcome: 'retained',
      checkpointScore: 1,
      correct: true,
      misconceptionId: misconception.id,
      misconceptionVerdict: 'repaired',
      referenceTime: new Date('2026-01-02T00:00:00Z'),
    });

    assert.ok(attemptId > 0);
    const counts = await store.query(`
      SELECT
        (SELECT count(*) FROM evidence WHERE student_id=$1 AND kind='review_attempt') AS evidence_count,
        (SELECT count(*) FROM review_attempts WHERE student_id=$1) AS review_count,
        (SELECT count(*) FROM learning_events WHERE student_id=$1 AND event_type='review.attempted') AS event_count,
        (SELECT count(*) FROM learning_events WHERE student_id=$1 AND event_type='evidence.recorded') AS evidence_event_count`, [studentId]);
    assert.deepEqual(counts.rows[0], {
      evidence_count: '1', review_count: '1', event_count: '1', evidence_event_count: '2',
    });

    assert.equal((await store.getMastery(studentId)).forces, 100);
    const state = await store.getMisconceptionState(misconception.id);
    assert.equal(state?.positiveEvidence, 1);
    assert.equal(state?.confidence, 0);
    assert.equal((await store.listDueReviews(studentId, '2026-01-02T23:59:59.999Z')).length, 0);
    const futureReview = await store.query('SELECT interval_days, streak, last_score FROM concept_reviews WHERE student_id=$1 AND concept_id=$2', [studentId, 'forces']);
    assert.deepEqual(futureReview.rows[0], { interval_days: 2, streak: 1, last_score: 1 });
  } finally {
    await pool.query('DELETE FROM students WHERE id=$1', [studentId]);
    await store.close();
  }
});

test('PostgreSQL review outcome rolls back every side effect on constraint failure', async (t) => {
  if (!process.env.DATABASE_URL) return t.skip('DATABASE_URL is required for PostgreSQL integration tests');
  const pool = createPostgresPool();
  const store = new PostgresLearningStore(pool);
  const nickname = `review-rollback-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const studentId = await store.ensureStudent(nickname);
  try {
    await store.scheduleReview(studentId, 'forces', 0, new Date('2026-01-01T00:00:00Z'));
    const before = await store.query(`SELECT
      (SELECT count(*) FROM evidence WHERE student_id=$1) AS evidence_count,
      (SELECT count(*) FROM review_attempts WHERE student_id=$1) AS review_count,
      (SELECT count(*) FROM learning_events WHERE student_id=$1) AS event_count`, [studentId]);

    await assert.rejects(
      store.recordReviewOutcomeAtomic({
        studentId,
        conceptId: 'forces',
        problemId: 'force-motion-transfer-1',
        evidence: { kind: 'review_attempt', value: 1, problemId: 'force-motion-transfer-1', reasoning: 'rollback' },
        outcome: 'retained', checkpointScore: 2, correct: true,
        misconceptionId: null, misconceptionVerdict: 'insufficient_evidence',
        referenceTime: new Date('2026-01-02T00:00:00Z'),
      }),
      /review_attempts_checkpoint_score_check/i,
    );

    const after = await store.query(`SELECT
      (SELECT count(*) FROM evidence WHERE student_id=$1) AS evidence_count,
      (SELECT count(*) FROM review_attempts WHERE student_id=$1) AS review_count,
      (SELECT count(*) FROM learning_events WHERE student_id=$1) AS event_count`, [studentId]);
    assert.deepEqual(after.rows[0], before.rows[0]);
    const review = await store.query('SELECT interval_days, streak, last_score FROM concept_reviews WHERE student_id=$1 AND concept_id=$2', [studentId, 'forces']);
    assert.deepEqual(review.rows[0], { interval_days: 1, streak: 0, last_score: 0 });
  } finally {
    await pool.query('DELETE FROM students WHERE id=$1', [studentId]);
    await store.close();
  }
});
