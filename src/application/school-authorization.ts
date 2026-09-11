import type { Pool } from 'pg';

export type SchoolRole = 'teacher' | 'dean' | 'admin';

export interface StaffIdentity {
  staffId: number;
  schoolId: number;
  role: SchoolRole;
  displayName: string;
}

export async function getStaffIdentity(pool: Pool, staffId: number): Promise<StaffIdentity> {
  const result = await pool.query(
    `SELECT id, school_id, display_name, role FROM school_staff WHERE id=$1`,
    [staffId],
  );
  if (result.rowCount !== 1) throw new Error('unknown school staff');
  const row = result.rows[0] as { id: number; school_id: number; display_name: string; role: SchoolRole };
  return { staffId: Number(row.id), schoolId: Number(row.school_id), displayName: row.display_name, role: row.role };
}

export async function authorizeClassroom(pool: Pool, staffId: number, classroomId: number): Promise<StaffIdentity> {
  const identity = await getStaffIdentity(pool, staffId);
  const access = await pool.query(
    `SELECT 1
       FROM classrooms c
      WHERE c.id=$1
        AND c.school_id=$2
        AND (
          $3 IN ('dean','admin')
          OR EXISTS (
            SELECT 1 FROM classroom_staff cs
             WHERE cs.classroom_id=c.id AND cs.staff_id=$4
          )
        )`,
    [classroomId, identity.schoolId, identity.role, identity.staffId],
  );
  if (access.rowCount !== 1) throw new Error('classroom authorization required');
  return identity;
}

export async function authorizeStudentInClassroom(pool: Pool, staffId: number, classroomId: number, studentId: number): Promise<StaffIdentity> {
  const identity = await authorizeClassroom(pool, staffId, classroomId);
  const result = await pool.query(
    `SELECT 1 FROM classroom_students WHERE classroom_id=$1 AND student_id=$2`,
    [classroomId, studentId],
  );
  if (result.rowCount !== 1) throw new Error('student is not in the authorized classroom');
  return identity;
}

export async function createSchool(pool: Pool, name: string, code: string): Promise<number> {
  const result = await pool.query(
    `INSERT INTO schools(name,code) VALUES($1,$2) RETURNING id`,
    [name.trim(), code.trim().toUpperCase()],
  );
  return Number(result.rows[0].id);
}

export async function createStaff(pool: Pool, schoolId: number, displayName: string, role: SchoolRole): Promise<number> {
  const result = await pool.query(
    `INSERT INTO school_staff(school_id,display_name,role) VALUES($1,$2,$3) RETURNING id`,
    [schoolId, displayName.trim(), role],
  );
  return Number(result.rows[0].id);
}

export async function assignStaffToClassroom(pool: Pool, classroomId: number, staffId: number): Promise<void> {
  await pool.query(
    `INSERT INTO classroom_staff(classroom_id,staff_id) VALUES($1,$2) ON CONFLICT DO NOTHING`,
    [classroomId, staffId],
  );
}

export async function createAuthorizedClassroom(pool: Pool, staffId: number, name: string, code: string): Promise<number> {
  const identity = await getStaffIdentity(pool, staffId);
  if (identity.role !== 'admin' && identity.role !== 'dean') throw new Error('classroom management authorization required');
  const result = await pool.query(
    `INSERT INTO classrooms(school_id,name,code) VALUES($1,$2,$3) RETURNING id`,
    [identity.schoolId, name.trim(), code.trim().toUpperCase()],
  );
  return Number(result.rows[0].id);
}
