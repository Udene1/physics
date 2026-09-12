import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { runMigrations } from '../src/infrastructure/migrate.js';
import { createSchool, createStaff, createAuthorizedClassroom, assignStaffToClassroom } from '../src/application/school-authorization.js';
import { enrollStudent } from '../src/application/classroom-intelligence.js';
import { getSchoolIntelligence } from '../src/application/school-intelligence.js';

test('school intelligence aggregates only classrooms belonging to the school', async (t) => {
  if (!process.env.DATABASE_URL) return t.skip('DATABASE_URL is required for PostgreSQL integration tests');
  const pool = createPostgresPool();
  await runMigrations(pool);
  const suffix = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const schoolA = await createSchool(pool, `Intelligence A ${suffix}`, `IA${Date.now()}`);
  const schoolB = await createSchool(pool, `Intelligence B ${suffix}`, `IB${Date.now()}`);
  const deanA = await createStaff(pool, schoolA, `Dean A ${suffix}`, 'dean');
  const deanB = await createStaff(pool, schoolB, `Dean B ${suffix}`, 'dean');
  const classA = await createAuthorizedClassroom(pool, deanA, `Physics A ${suffix}`, `PA${Date.now()}`);
  const classB = await createAuthorizedClassroom(pool, deanB, `Physics B ${suffix}`, `PB${Date.now()}`);
  const studentA = Number((await pool.query('INSERT INTO students(nickname) VALUES($1) RETURNING id', [`school-intel-a-${suffix}`])).rows[0].id);
  const studentB = Number((await pool.query('INSERT INTO students(nickname) VALUES($1) RETURNING id', [`school-intel-b-${suffix}`])).rows[0].id);
  try {
    await assignStaffToClassroom(pool, classA, deanA);
    await assignStaffToClassroom(pool, classB, deanB);
    await enrollStudent(pool, classA, studentA);
    await enrollStudent(pool, classB, studentB);
    await pool.query("INSERT INTO mastery(student_id,concept_id,score,attempts,correct) VALUES($1,'forces',80,2,2)", [studentA]);
    await pool.query("INSERT INTO mastery(student_id,concept_id,score,attempts,correct) VALUES($1,'forces',40,2,1)", [studentB]);
    const intelligence = await getSchoolIntelligence(pool, schoolA);
    assert.equal(intelligence.schoolId, schoolA);
    assert.equal(intelligence.students, 1);
    assert.equal(intelligence.classrooms.length, 1);
    assert.equal(intelligence.classrooms[0]?.classroomId, classA);
    assert.equal(intelligence.averageMastery, 80);
    assert.equal(intelligence.classrooms[0]?.averageMastery, 80);
    assert.equal(intelligence.classrooms.some((c) => c.classroomId === classB), false);
  } finally {
    await pool.query('DELETE FROM students WHERE id IN ($1,$2)', [studentA, studentB]);
    await pool.query('DELETE FROM schools WHERE id IN ($1,$2)', [schoolA, schoolB]);
    await pool.end();
  }
});
