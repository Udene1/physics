import type { Pool } from 'pg';

export interface SchoolIntelligence {
  schoolId: number;
  schoolName: string;
  classrooms: Array<{
    classroomId: number;
    name: string;
    code: string;
    students: number;
    averageMastery: number | null;
    activeMisconceptions: number;
    remediationAttempts: number;
    repairedRemediations: number;
    repairRate: number | null;
  }>;
  students: number;
  averageMastery: number | null;
  activeMisconceptions: number;
  remediationAttempts: number;
  repairedRemediations: number;
  repairRate: number | null;
}

export async function getSchoolIntelligence(pool: Pool, schoolId: number): Promise<SchoolIntelligence> {
  const school = await pool.query('SELECT id,name FROM schools WHERE id=$1', [schoolId]);
  if (school.rowCount !== 1) throw new Error('Unknown school');

  // Aggregate each learner signal independently. Joining roster, mastery,
  // misconceptions and remediation rows in one relation multiplies facts
  // (for example 3 mastery rows × 2 misconceptions × 4 attempts).
  const result = await pool.query(`
    WITH roster AS (
      SELECT c.id AS classroom_id, c.name, c.code,
        COUNT(DISTINCT cs.student_id)::int AS students
      FROM classrooms c
      LEFT JOIN classroom_students cs ON cs.classroom_id=c.id
      WHERE c.school_id=$1
      GROUP BY c.id,c.name,c.code
    ),
    mastery AS (
      SELECT cs.classroom_id,
        AVG(m.score) FILTER (WHERE m.attempts > 0)::double precision AS average_mastery
      FROM classroom_students cs
      JOIN mastery m ON m.student_id=cs.student_id
      JOIN classrooms c ON c.id=cs.classroom_id
      WHERE c.school_id=$1
      GROUP BY cs.classroom_id
    ),
    misconceptions AS (
      SELECT cs.classroom_id,
        COUNT(DISTINCT mx.id) FILTER (WHERE mx.status='active')::int AS active_misconceptions
      FROM classroom_students cs
      JOIN classrooms c ON c.id=cs.classroom_id
      LEFT JOIN misconceptions mx ON mx.student_id=cs.student_id
      WHERE c.school_id=$1
      GROUP BY cs.classroom_id
    ),
    remediation AS (
      SELECT cs.classroom_id,
        COUNT(ra.id)::int AS remediation_attempts,
        COUNT(ra.id) FILTER (WHERE ra.verdict='repaired')::int AS repaired_remediations
      FROM classroom_students cs
      JOIN classrooms c ON c.id=cs.classroom_id
      JOIN interventions i ON i.student_id=cs.student_id
      JOIN remediation_attempts ra ON ra.intervention_id=i.id
      WHERE c.school_id=$1
      GROUP BY cs.classroom_id
    )
    SELECT r.classroom_id,r.name,r.code,r.students,
      m.average_mastery,
      COALESCE(x.active_misconceptions,0)::int AS active_misconceptions,
      COALESCE(a.remediation_attempts,0)::int AS remediation_attempts,
      COALESCE(a.repaired_remediations,0)::int AS repaired_remediations
    FROM roster r
    LEFT JOIN mastery m ON m.classroom_id=r.classroom_id
    LEFT JOIN misconceptions x ON x.classroom_id=r.classroom_id
    LEFT JOIN remediation a ON a.classroom_id=r.classroom_id
    ORDER BY r.name,r.classroom_id`, [schoolId]);

  const classrooms = result.rows.map((row) => {
    const attempts = Number(row.remediation_attempts ?? 0);
    const repaired = Number(row.repaired_remediations ?? 0);
    return {
      classroomId: Number(row.classroom_id), name: String(row.name), code: String(row.code),
      students: Number(row.students ?? 0),
      averageMastery: row.average_mastery == null ? null : Number(row.average_mastery),
      activeMisconceptions: Number(row.active_misconceptions ?? 0),
      remediationAttempts: attempts, repairedRemediations: repaired,
      repairRate: attempts === 0 ? null : repaired / attempts,
    };
  });

  const totals = classrooms.reduce((a, c) => ({
    students: a.students + c.students,
    activeMisconceptions: a.activeMisconceptions + c.activeMisconceptions,
    remediationAttempts: a.remediationAttempts + c.remediationAttempts,
    repairedRemediations: a.repairedRemediations + c.repairedRemediations,
    masteryWeightedSum: a.masteryWeightedSum + (c.averageMastery ?? 0) * c.students,
    masteryStudents: a.masteryStudents + (c.averageMastery == null ? 0 : c.students),
  }), { students: 0, activeMisconceptions: 0, remediationAttempts: 0, repairedRemediations: 0, masteryWeightedSum: 0, masteryStudents: 0 });

  return {
    schoolId,
    schoolName: String(school.rows[0].name),
    classrooms,
    students: totals.students,
    averageMastery: totals.masteryStudents === 0 ? null : totals.masteryWeightedSum / totals.masteryStudents,
    activeMisconceptions: totals.activeMisconceptions,
    remediationAttempts: totals.remediationAttempts,
    repairedRemediations: totals.repairedRemediations,
    repairRate: totals.remediationAttempts === 0 ? null : totals.repairedRemediations / totals.remediationAttempts,
  };
}
