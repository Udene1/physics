import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { runMigrations } from '../src/infrastructure/migrate.js';

test('learning artifact usage links generated content to the evidence it produced', async (t) => {
  if (!process.env.DATABASE_URL) return t.skip('DATABASE_URL is required for PostgreSQL integration tests');
  const pool = createPostgresPool();
  await runMigrations(pool);
  const nickname = `artifact-usage-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  let studentId: number | undefined;
  try {
    const student = await pool.query('INSERT INTO students(nickname) VALUES($1) RETURNING id', [nickname]);
    studentId = Number(student.rows[0].id);
    const artifact = await pool.query(
      `INSERT INTO learning_artifacts(artifact_kind,content,training_eligible,retention_class)
       VALUES('remediation_problem',$1,false,'standard') RETURNING id`,
      [JSON.stringify({ problem: 'A block is pushed...' })],
    );
    const evidence = await pool.query(
      `INSERT INTO evidence(student_id,concept_id,kind,problem_id,reasoning)
       VALUES($1,'forces','remediation_attempt','force-motion-1','F_net = ma') RETURNING id`,
      [studentId],
    );
    const usage = await pool.query(
      `INSERT INTO learning_artifact_usage(artifact_id,student_id,evidence_id,usage_kind)
       VALUES($1,$2,$3,'presented') RETURNING artifact_id,student_id,evidence_id,usage_kind`,
      [artifact.rows[0].id, studentId, evidence.rows[0].id],
    );
    assert.equal(Number(usage.rows[0].artifact_id), Number(artifact.rows[0].id));
    assert.equal(Number(usage.rows[0].student_id), studentId);
    assert.equal(Number(usage.rows[0].evidence_id), Number(evidence.rows[0].id));
    assert.equal(usage.rows[0].usage_kind, 'presented');
  } finally {
    if (studentId !== undefined) await pool.query('DELETE FROM students WHERE id=$1', [studentId]);
    await pool.end();
  }
});
