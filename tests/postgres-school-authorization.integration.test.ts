import assert from 'node:assert/strict';
import test from 'node:test';
import { createPostgresPool } from '../src/infrastructure/postgres.js';
import { runMigrations } from '../src/infrastructure/migrate.js';
import { authorizeClassroom, authorizeStudentInClassroom, createSchool, createStaff, assignStaffToClassroom, createAuthorizedClassroom } from '../src/application/school-authorization.js';
import { enrollStudent } from '../src/application/classroom-intelligence.js';

test('school authorization isolates teachers and permits explicitly shared classes', async (t) => {
  if (!process.env.DATABASE_URL) return t.skip('DATABASE_URL is required for PostgreSQL integration tests');
  const pool = createPostgresPool(); await runMigrations(pool);
  const suffix = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const schoolA = await createSchool(pool, `School A ${suffix}`, `SA${Date.now()}`);
  const schoolB = await createSchool(pool, `School B ${suffix}`, `SB${Date.now()}`);
  const teacherA = await createStaff(pool, schoolA, `Teacher A ${suffix}`, 'teacher');
  const teacherB = await createStaff(pool, schoolA, `Teacher B ${suffix}`, 'teacher');
  const teacherOtherSchool = await createStaff(pool, schoolB, `Teacher Other ${suffix}`, 'teacher');
  const deanA = await createStaff(pool, schoolA, `Dean A ${suffix}`, 'dean');
  const classOne = await createAuthorizedClassroom(pool, deanA, `Class One ${suffix}`, `C1${Date.now()}`);
  const classTwo = await createAuthorizedClassroom(pool, deanA, `Class Two ${suffix}`, `C2${Date.now()}`);
  const studentId = Number((await pool.query('INSERT INTO students(nickname) VALUES($1) RETURNING id', [`auth-student-${suffix}`])).rows[0].id);
  try {
    await assignStaffToClassroom(pool, classOne, teacherA);
    await assignStaffToClassroom(pool, classOne, teacherB);
    await enrollStudent(pool, classOne, studentId);
    assert.equal((await authorizeClassroom(pool, teacherA, classOne)).staffId, teacherA);
    assert.equal((await authorizeClassroom(pool, teacherB, classOne)).staffId, teacherB);
    assert.equal((await authorizeClassroom(pool, deanA, classTwo)).role, 'dean');
    await assert.rejects(() => authorizeClassroom(pool, teacherA, classTwo), /classroom authorization required/);
    await assert.rejects(() => authorizeClassroom(pool, teacherOtherSchool, classOne), /classroom authorization required/);
    await assert.rejects(() => authorizeStudentInClassroom(pool, teacherA, classTwo, studentId), /classroom authorization required/);
    await assert.rejects(() => authorizeStudentInClassroom(pool, teacherA, classOne, studentId + 999999), /student is not in the authorized classroom/);
  } finally {
    await pool.query('DELETE FROM students WHERE id=$1', [studentId]);
    await pool.query('DELETE FROM schools WHERE id IN ($1,$2)', [schoolA, schoolB]);
    await pool.end();
  }
});

test('database rejects assigning staff across schools', async (t) => {
  if (!process.env.DATABASE_URL) return t.skip('DATABASE_URL is required for PostgreSQL integration tests');
  const pool = createPostgresPool(); await runMigrations(pool);
  const suffix = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const schoolA = await createSchool(pool, `Guard A ${suffix}`, `GA${Date.now()}`);
  const schoolB = await createSchool(pool, `Guard B ${suffix}`, `GB${Date.now()}`);
  const deanA = await createStaff(pool, schoolA, `Guard Dean ${suffix}`, 'dean');
  const teacherB = await createStaff(pool, schoolB, `Guard Teacher ${suffix}`, 'teacher');
  const classroom = await createAuthorizedClassroom(pool, deanA, `Guard Class ${suffix}`, `G${Date.now()}`);
  try { await assert.rejects(() => assignStaffToClassroom(pool, classroom, teacherB), /staff cannot be assigned across schools/); }
  finally { await pool.query('DELETE FROM schools WHERE id IN ($1,$2)', [schoolA, schoolB]); await pool.end(); }
});
