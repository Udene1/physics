import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { runMigrations } from '../src/infrastructure/migrate.js';
import { createClassroom, enrollStudent, getClassroomIntelligence } from '../src/application/classroom-intelligence.js';

test('classroom intelligence identifies cohort patterns, attention, and bottlenecks', async (t) => {
  if (!process.env.DATABASE_URL) return t.skip('DATABASE_URL is required for PostgreSQL integration tests');
  const pool = createPostgresPool(); await runMigrations(pool);
  const suffix = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const studentOne = Number((await pool.query('INSERT INTO students(nickname) VALUES($1) RETURNING id', [`class-one-${suffix}`])).rows[0].id);
  const studentTwo = Number((await pool.query('INSERT INTO students(nickname) VALUES($1) RETURNING id', [`class-two-${suffix}`])).rows[0].id);
  const classroomId = await createClassroom(pool, 'Founding Physics', `VITA${Date.now()}`);
  try {
    await enrollStudent(pool, classroomId, studentOne); await enrollStudent(pool, classroomId, studentTwo);
    await pool.query(`INSERT INTO mastery(student_id,concept_id,score,attempts,correct) VALUES($1,'forces',80,5,4),($2,'forces',40,5,2)`, [studentOne, studentTwo]);
    const e1 = Number((await pool.query(`INSERT INTO evidence(student_id,concept_id,kind,value) VALUES($1,'forces','attempt',0) RETURNING id`, [studentOne])).rows[0].id);
    const e2 = Number((await pool.query(`INSERT INTO evidence(student_id,concept_id,kind,value) VALUES($1,'forces','attempt',0) RETURNING id`, [studentTwo])).rows[0].id);
    const m1 = Number((await pool.query(`INSERT INTO misconceptions(student_id,concept_id,code,severity,occurrences,last_evidence_id) VALUES($1,'forces','force-causes-motion',4,3,$2) RETURNING id`, [studentOne, e1])).rows[0].id);
    const m2 = Number((await pool.query(`INSERT INTO misconceptions(student_id,concept_id,code,severity,occurrences,last_evidence_id) VALUES($1,'forces','force-causes-motion',3,2,$2) RETURNING id`, [studentTwo, e2])).rows[0].id);
    await pool.query(`INSERT INTO misconception_state(misconception_id,confidence,positive_evidence,negative_evidence,last_verdict) VALUES($1,75,0,3,'still_present'),($2,50,0,2,'still_present')`, [m1, m2]);
    const i1 = Number((await pool.query(`INSERT INTO interventions(student_id,misconception_id,concept_id,prerequisite_concept_id,problem_id,stage,strategy) VALUES($1,$2,'forces','motion','force-motion-discrimination-1','discrimination','separate force from motion') RETURNING id`, [studentOne, m1])).rows[0].id);
    await pool.query(`INSERT INTO remediation_attempts(intervention_id,evidence_id,verdict,checkpoint_score) VALUES($1,$2,'repaired',1)`, [i1, e1]);
    await pool.query(`INSERT INTO concept_reviews(student_id,concept_id,due_at,interval_days,streak,last_score) VALUES($1,'forces',now()-interval '1 hour',1,1,1)`, [studentOne]);
    const summary = await getClassroomIntelligence(pool, classroomId);
    assert.equal(summary.students, 2); assert.equal(summary.interventionEffectiveness.attempts, 1); assert.equal(summary.interventionEffectiveness.repaired, 1);
    assert.equal(summary.interventionEffectiveness.repairRate, 1); assert.ok(summary.attention.some((x) => x.studentId === studentOne && x.attention === 'high'));
    assert.equal(summary.bottlenecks.length, 1); assert.equal(summary.bottlenecks[0].conceptId, 'forces'); assert.equal(summary.bottlenecks[0].averageMastery, 60);
    assert.match(summary.bottlenecks[0].reason, /below 60%/);
  } finally { await pool.query('DELETE FROM students WHERE id IN ($1,$2)', [studentOne, studentTwo]); await pool.query('DELETE FROM classrooms WHERE id=$1', [classroomId]); await pool.end(); }
});

test('classroom enrollment is idempotent', async (t) => {
  if (!process.env.DATABASE_URL) return t.skip('DATABASE_URL is required for PostgreSQL integration tests');
  const pool = createPostgresPool(); await runMigrations(pool);
  const suffix = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const studentId = Number((await pool.query('INSERT INTO students(nickname) VALUES($1) RETURNING id', [`class-idempotent-${suffix}`])).rows[0].id);
  const classroomId = await createClassroom(pool, 'Idempotent Class', `IDEM${Date.now()}`);
  try { await enrollStudent(pool, classroomId, studentId); await enrollStudent(pool, classroomId, studentId); const result = await pool.query('SELECT count(*)::int AS count FROM classroom_students WHERE classroom_id=$1 AND student_id=$2', [classroomId, studentId]); assert.equal(Number(result.rows[0].count), 1); }
  finally { await pool.query('DELETE FROM students WHERE id=$1', [studentId]); await pool.query('DELETE FROM classrooms WHERE id=$1', [classroomId]); await pool.end(); }
});
