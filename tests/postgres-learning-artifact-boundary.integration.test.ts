import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { runMigrations } from '../src/infrastructure/migrate.js';
import { recordArtifactAndUsage, recordGeneratedArtifact, recordArtifactUsage } from '../src/infrastructure/learning-artifacts.js';

test('generated artifact boundary persists provenance and usage atomically', async (t) => {
  if (!process.env.DATABASE_URL) return t.skip('DATABASE_URL is required for PostgreSQL integration tests');
  const pool = createPostgresPool();
  await runMigrations(pool);
  const nickname = `artifact-boundary-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  let studentId: number | undefined;
  try {
    const student = await pool.query('INSERT INTO students(nickname) VALUES($1) RETURNING id', [nickname]);
    studentId = Number(student.rows[0].id);
    const artifact = await recordGeneratedArtifact(pool, { studentId, artifactKind: 'remediation_problem', content: { problemId: 'force-motion-transfer-1' }, generationContext: { misconception: 'force-causes-motion' }, modelProvider: 'provider', modelName: 'model', modelVersion: 'v1', promptTemplateVersion: 'remediation-v1', curriculumVersion: 'physics-v1' });
    assert.equal(artifact.studentId, studentId);
    assert.equal(artifact.trainingEligible, false);
    assert.equal(artifact.validationStatus, 'unvalidated');
    const evidence = await pool.query(`INSERT INTO evidence(student_id,concept_id,kind,problem_id,reasoning) VALUES($1,'forces','remediation_attempt','force-motion-transfer-1','F_net = ma') RETURNING id`, [studentId]);
    await recordArtifactAndUsage(pool, { studentId, artifactKind: 'review_problem', content: { problemId: 'force-motion-transfer-1' } }, 'presented', Number(evidence.rows[0].id));
    const usage = await pool.query(`SELECT u.usage_kind,u.student_id,u.evidence_id,a.artifact_kind FROM learning_artifact_usage u JOIN learning_artifacts a ON a.id=u.artifact_id WHERE u.student_id=$1 ORDER BY u.id`, [studentId]);
    assert.equal(usage.rows.length, 1);
    assert.equal(usage.rows[0].usage_kind, 'presented');
    assert.equal(Number(usage.rows[0].evidence_id), Number(evidence.rows[0].id));
    assert.equal(usage.rows[0].artifact_kind, 'review_problem');
  } finally {
    if (studentId !== undefined) await pool.query('DELETE FROM students WHERE id=$1', [studentId]);
    await pool.end();
  }
});

test('artifact usage rejects cross-learner attribution and rolls back the usage write', async (t) => {
  if (!process.env.DATABASE_URL) return t.skip('DATABASE_URL is required for PostgreSQL integration tests');
  const pool = createPostgresPool();
  await runMigrations(pool);
  const suffix = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  let first: number | undefined;
  let second: number | undefined;
  try {
    first = Number((await pool.query('INSERT INTO students(nickname) VALUES($1) RETURNING id', [`artifact-owner-${suffix}`])).rows[0].id);
    second = Number((await pool.query('INSERT INTO students(nickname) VALUES($1) RETURNING id', [`artifact-other-${suffix}`])).rows[0].id);
    const artifact = await recordGeneratedArtifact(pool, { studentId: first, artifactKind: 'explanation', content: { text: 'force changes velocity through acceleration' } });
    const evidence = await pool.query(`INSERT INTO evidence(student_id,concept_id,kind,reasoning) VALUES($1,'forces','attempt','force changes velocity') RETURNING id`, [second]);
    await assert.rejects(recordArtifactUsage(pool, artifact.id, 'presented', second, Number(evidence.rows[0].id)), /does not match/);
    const usage = await pool.query('SELECT COUNT(*)::int AS count FROM learning_artifact_usage WHERE artifact_id=$1', [artifact.id]);
    assert.equal(Number(usage.rows[0].count), 0);
  } finally {
    if (first !== undefined) await pool.query('DELETE FROM students WHERE id=$1', [first]);
    if (second !== undefined) await pool.query('DELETE FROM students WHERE id=$1', [second]);
    await pool.end();
  }
});
