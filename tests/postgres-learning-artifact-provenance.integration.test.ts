import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { runMigrations } from '../src/infrastructure/migrate.js';

test('generated learning artifacts retain provenance without becoming training data by default', async (t) => {
  if (!process.env.DATABASE_URL) return t.skip('DATABASE_URL is required for PostgreSQL integration tests');
  const pool = createPostgresPool();
  await runMigrations(pool);
  const nickname = `artifact-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  let studentId: number | undefined;
  try {
    const student = await pool.query('INSERT INTO students(nickname) VALUES($1) RETURNING id', [nickname]);
    studentId = Number(student.rows[0].id);

    const result = await pool.query(
      `INSERT INTO learning_artifacts(
         student_id,artifact_kind,content,generation_context,model_provider,model_name,model_version,
         prompt_template_version,curriculum_version,validation_status,training_eligible,retention_class
       ) VALUES($1,'remediation_problem',$2,$3,'test-provider','test-model','v1','remediation-v3','forces-v1','validated',false,'standard')
       RETURNING id,artifact_kind,model_provider,model_name,model_version,prompt_template_version,curriculum_version,validation_status,training_eligible,retention_class,student_id`,
      [studentId, JSON.stringify({ problem: 'A block is pushed...' }), JSON.stringify({ misconception: 'force_causes_motion', concept: 'forces' })],
    );

    assert.deepEqual(result.rows[0], {
      id: result.rows[0].id,
      artifact_kind: 'remediation_problem',
      model_provider: 'test-provider',
      model_name: 'test-model',
      model_version: 'v1',
      prompt_template_version: 'remediation-v3',
      curriculum_version: 'forces-v1',
      validation_status: 'validated',
      training_eligible: false,
      retention_class: 'standard',
      student_id: studentId,
    });

    const stored = await pool.query('SELECT content,generation_context FROM learning_artifacts WHERE id=$1', [result.rows[0].id]);
    assert.equal(stored.rows[0].content.problem, 'A block is pushed...');
    assert.equal(stored.rows[0].generation_context.misconception, 'force_causes_motion');
  } finally {
    if (studentId !== undefined) await pool.query('DELETE FROM students WHERE id=$1', [studentId]);
    await pool.end();
  }
});
