import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { runMigrations } from '../src/infrastructure/migrate.js';
import { createSchool, createStaff, createAuthorizedClassroom } from '../src/application/school-authorization.js';
import { enrollStudent } from '../src/application/classroom-intelligence.js';
import { getSchoolIntelligence } from '../src/application/school-intelligence.js';

test('school intelligence counts remediation attempts independently from learner joins', async (t) => {
  if (!process.env.DATABASE_URL) return t.skip('DATABASE_URL is required for PostgreSQL integration tests');
  const pool = createPostgresPool(); await runMigrations(pool);
  const suffix = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const schoolId = await createSchool(pool, `Aggregation School ${suffix}`, `AG${Date.now()}`);
  const deanId = await createStaff(pool, schoolId, `Dean ${suffix}`, 'dean');
  const classroomId = await createAuthorizedClassroom(pool, deanId, `Physics ${suffix}`, `PH${Date.now()}`);
  const studentA = Number((await pool.query('INSERT INTO students(nickname) VALUES($1) RETURNING id', [`agg-a-${suffix}`])).rows[0].id);
  const studentB = Number((await pool.query('INSERT INTO students(nickname) VALUES($1) RETURNING id', [`agg-b-${suffix}`])).rows[0].id);
  try {
    await enrollStudent(pool, classroomId, studentA); await enrollStudent(pool, classroomId, studentB);
    await pool.query("INSERT INTO mastery(student_id,concept_id,score,attempts,correct) VALUES ($1,'forces',80,5,4),($2,'forces',60,5,3)", [studentA, studentB]);
    const misconception = Number((await pool.query("INSERT INTO misconceptions(student_id,concept_id,code,severity) VALUES($1,'forces','force_causes_motion',4) RETURNING id", [studentA])).rows[0].id);
    await pool.query('INSERT INTO misconception_state(misconception_id,confidence,negative_evidence) VALUES($1,70,2)', [misconception]);
    const intervention = Number((await pool.query("INSERT INTO interventions(student_id,misconception_id,concept_id,prerequisite_concept_id,problem_id,stage,strategy) VALUES($1,$2,'forces','motion','force-motion-discrimination-1','discrimination','contrast sustained motion with acceleration') RETURNING id", [studentA, misconception])).rows[0].id);
    const evidenceA = Number((await pool.query("INSERT INTO evidence(student_id,concept_id,kind,value,problem_id,reasoning) VALUES($1,'forces','remediation_attempt',1,'force-motion-discrimination-1','F_net = ma') RETURNING id", [studentA])).rows[0].id);
    const evidenceB = Number((await pool.query("INSERT INTO evidence(student_id,concept_id,kind,value,problem_id,reasoning) VALUES($1,'forces','remediation_attempt',1,'force-motion-discrimination-1','F_net = ma') RETURNING id", [studentA])).rows[0].id);
    await pool.query("INSERT INTO remediation_attempts(intervention_id,evidence_id,verdict,checkpoint_score) VALUES($1,$2,'repaired',1),($1,$3,'insufficient_evidence',0.5)", [intervention, evidenceA, evidenceB]);
    const intelligence = await getSchoolIntelligence(pool, schoolId);
    assert.equal(intelligence.students, 2); assert.equal(intelligence.averageMastery, 70); assert.equal(intelligence.activeMisconceptions, 1);
    assert.equal(intelligence.remediationAttempts, 2); assert.equal(intelligence.repairedRemediations, 1); assert.equal(intelligence.repairRate, 0.5);
    assert.equal(intelligence.classrooms[0]?.remediationAttempts, 2); assert.equal(intelligence.classrooms[0]?.repairedRemediations, 1);
  } finally {
    await pool.query('DELETE FROM students WHERE id IN ($1,$2)', [studentA, studentB]); await pool.query('DELETE FROM schools WHERE id=$1', [schoolId]); await pool.end();
  }
});
