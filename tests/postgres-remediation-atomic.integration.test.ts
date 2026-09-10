import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { PostgresLearningStore } from '../src/infrastructure/postgres-store.js';

const databaseUrl = process.env.DATABASE_URL;

test('PostgreSQL remediation transaction rolls back every write on invariant failure', async (t) => {
  if (!databaseUrl) { t.skip('DATABASE_URL is required for the PostgreSQL integration suite'); return; }
  const pool = createPostgresPool();
  const store = new PostgresLearningStore(pool);
  const nickname = `pg-atomic-${process.pid}-${Date.now()}`;
  try {
    const studentId = await store.ensureStudent(nickname);
    const seedEvidence = await store.addEvidence(studentId, 'forces', { kind: 'diagnostic', reasoning: 'seed' });
    const misconception = await store.upsertMisconception(studentId, 'forces', 'force_causes_motion', 2, seedEvidence);
    const intervention = await store.queueIntervention(studentId, misconception.id, 'forces', 'vectors', 'force-motion-discrimination-1', 'discrimination', 'separate force from motion');

    await assert.rejects(
      store.recordRemediationOutcomeAtomic!({
        studentId,
        interventionId: intervention.id,
        interventionMisconceptionId: misconception.id,
        conceptId: 'forces',
        problemId: 'force-motion-discrimination-1',
        evidence: { kind: 'remediation_attempt', note: '2 N', reasoning: 'F_net = ma' },
        verdict: 'repaired',
        checkpointScore: 1,
        correct: true,
        signalMisconceptionId: misconception.id,
        signalVerdict: 'repaired',
        completeIntervention: true,
        resolveMisconception: true,
      }),
      /cannot be resolved/i,
    );

    const counts = await pool.query(`
      SELECT
        (SELECT count(*) FROM evidence WHERE student_id=$1)::int AS evidence,
        (SELECT count(*) FROM remediation_attempts WHERE intervention_id=$2)::int AS attempts,
        (SELECT count(*) FROM interventions WHERE student_id=$1)::int AS interventions
    `, [studentId, intervention.id]);
    assert.equal(Number(counts.rows[0].evidence), 1);
    assert.equal(Number(counts.rows[0].attempts), 0);
    assert.equal(Number(counts.rows[0].interventions), 1);

    const persistedIntervention = await store.getIntervention(intervention.id);
    assert.equal(persistedIntervention?.status, 'queued');
    const state = await store.getMisconceptionState(misconception.id);
    assert.equal(state?.positiveEvidence, 0);
    assert.equal(state?.confidence, 0);
  } finally {
    await pool.query('DELETE FROM students WHERE nickname=$1', [nickname]);
    await store.close();
  }
});
