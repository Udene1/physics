import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { runMigrations } from '../src/infrastructure/migrate.js';
import { PostgresLearningStore } from '../src/infrastructure/postgres-store.js';
import { PostgresLearningEngine } from '../src/application/postgres-learning-engine.js';

const url = process.env.DATABASE_URL;
const repairedReasoning = 'Constant velocity means zero acceleration. F_net = ma, so net force is 0 N. A net force changes velocity through acceleration; it does not sustain constant velocity.';
const transferReasoning = 'F_net = ma gives a = 4/2 = 2 m/s² east. Then v = u + at = 3 + 2(2) = 7 m/s east. The force changes velocity through acceleration.';
const reviewReasoning = 'Choose east as positive and west as negative. F_net = ma gives a = -2 m/s², so the acceleration is 2 m/s² west. Then v = u + at gives v = 0 m/s. The net force changes velocity through acceleration rather than sustaining motion.';

test('learner moves misconception -> discrimination -> transfer -> repair -> review', async (t) => {
  if (!url) { t.skip('DATABASE_URL is required for PostgreSQL integration tests'); return; }
  const pool = createPostgresPool();
  await runMigrations(pool);
  const store = new PostgresLearningStore(pool);
  const engine = new PostgresLearningEngine(store);
  const nickname = `journey-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  try {
    const studentId = await store.ensureStudent(nickname);
    await engine.start(studentId);
    await engine.recordStructuredAttempt(studentId, 'forces', { correct: false, reasoning: 'The cart is moving, so a force is needed to keep it moving.', problemId: 'forces-1', misconceptionCodes: ['force_causes_motion'], misconceptionSeverity: 3 });
    let intervention = await engine.nextIntervention(studentId);
    assert.ok(intervention); assert.equal(intervention.stage, 'discrimination'); assert.equal(intervention.problemId, 'force-motion-discrimination-1');
    const discrimination = await engine.submitRemediationAttempt(studentId, intervention.id, { reasoning: repairedReasoning, answer: '0 N' });
    assert.equal(discrimination.evaluation.verdict, 'repaired');
    intervention = await engine.nextIntervention(studentId);
    assert.ok(intervention); assert.equal(intervention.stage, 'transfer'); assert.equal(intervention.problemId, 'force-motion-transfer-1');
    const transfer = await engine.submitRemediationAttempt(studentId, intervention.id, { reasoning: transferReasoning, answer: '2 m/s² east; 7 m/s east' });
    assert.equal(transfer.evaluation.verdict, 'repaired'); assert.equal(transfer.snapshot.activeMisconceptions.length, 0);
    const resolved = (await store.listMisconceptions(studentId, 'forces')).find(m => m.code === 'force_causes_motion');
    assert.ok(resolved); assert.equal(resolved.status, 'resolved');
    const state = await store.getMisconceptionState(resolved.id); assert.ok(state); assert.ok(state.positiveEvidence >= 2); assert.ok(state.confidence <= 30);

    await store.scheduleReview(studentId, 'forces', 1, new Date(Date.now() - 2 * 24 * 60 * 60 * 1000));
    const due = await engine.nextReview(studentId);
    assert.ok(due); assert.equal(due.conceptId, 'forces');
    const review = await engine.submitReviewAttempt(studentId, { reasoning: reviewReasoning, answer: '2 m/s² west; 0 m/s; net force changes velocity rather than sustaining motion' });
    assert.equal(review.outcome, 'retained'); assert.ok(review.attemptId > 0);

    const events = await pool.query(`SELECT event_type FROM learning_events WHERE student_id=$1 ORDER BY id`, [studentId]);
    const types = events.rows.map(row => String(row.event_type));
    assert.ok(types.includes('evidence.recorded')); assert.ok(types.includes('misconception.created')); assert.ok(types.includes('intervention.queued')); assert.ok(types.includes('remediation.attempted')); assert.ok(types.includes('intervention.state_changed')); assert.ok(types.includes('misconception.state_changed')); assert.ok(types.includes('review.attempted'));
  } finally {
    const student = await pool.query('SELECT id FROM students WHERE nickname=$1', [nickname]);
    if (student.rowCount === 1) await pool.query('DELETE FROM students WHERE id=$1', [Number(student.rows[0].id)]);
    await pool.end();
  }
});
