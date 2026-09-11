import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { runMigrations } from '../src/infrastructure/migrate.js';
import { persistModelArtifact, recordModelArtifactUsage } from '../src/application/artifact-provenance.js';

const url = process.env.DATABASE_URL;

test('model artifact provenance is persisted and linked to learner evidence', async (t) => {
  if (!url) { t.skip('DATABASE_URL is required for PostgreSQL integration tests'); return; }
  const pool = createPostgresPool();
  await runMigrations(pool);
  const nickname = `artifact-service-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  try {
    const student = await pool.query('INSERT INTO students(nickname) VALUES($1) RETURNING id', [nickname]);
    const studentId = Number(student.rows[0].id);
    const artifact = await persistModelArtifact(pool, { text: 'A targeted force problem', provider: 'gemini', model: 'model-x' }, {
      studentId, artifactKind: 'remediation_problem', generationContext: { misconceptionCode: 'force_causes_motion', stage: 'discrimination' },
      promptTemplateVersion: 'remediation-v1', curriculumVersion: 'mechanics-v1',
    });
    assert.equal(artifact.studentId, studentId);
    assert.equal(artifact.modelProvider, 'gemini');
    assert.equal(artifact.modelName, 'model-x');
    assert.equal(artifact.trainingEligible, false);
    const evidence = await pool.query(`INSERT INTO evidence(student_id,concept_id,kind,value,problem_id,reasoning) VALUES($1,'forces','remediation_attempt',1,'artifact-problem','F_net = ma') RETURNING id`, [studentId]);
    const usageId = await recordModelArtifactUsage(pool, artifact.id, 'attempted', studentId, Number(evidence.rows[0].id));
    assert.ok(usageId > 0);
    const usage = await pool.query('SELECT student_id,evidence_id,usage_kind FROM learning_artifact_usage WHERE id=$1', [usageId]);
    assert.equal(Number(usage.rows[0].student_id), studentId);
    assert.equal(Number(usage.rows[0].evidence_id), Number(evidence.rows[0].id));
    assert.equal(usage.rows[0].usage_kind, 'attempted');
  } finally {
    const student = await pool.query('SELECT id FROM students WHERE nickname=$1', [nickname]);
    if (student.rowCount === 1) await pool.query('DELETE FROM students WHERE id=$1', [Number(student.rows[0].id)]);
    await pool.end();
  }
});
