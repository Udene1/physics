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

  const result = await pool.query(`
    SELECT c.id AS classroom_id, c.name, c.code,
      COUNT(DISTINCT cs.student_id)::int AS students,
      AVG(m.score) FILTER (WHERE m.attempts > 0)::double precision AS average_mastery,
      COUNT(DISTINCT mx.id) FILTER (WHERE mx.status='active')::int AS active_misconceptions,
      COUNT(ra.id)::int AS remediation_attempts,
      COUNT(ra.id) FILTER (WHERE ra.verdict='repaired')::int AS repaired_remediations
    FROM classrooms c
    LEFT JOIN classroom_students cs ON cs.classroom_id=c.id
    LEFT JOIN mastery m ON m.student_id=cs.student_id
    LEFT JOIN misconceptions mx ON mx.student_id=cs.student_id
    LEFT JOIN interventions i ON i.student_id=cs.student_id
    LEFT JOIN remediation_attempts ra ON ra.intervention_id=i.id
    WHERE c.school_id=$1
    GROUP BY c.id,c.name,c.code
    ORDER BY c.name,c.id`, [schoolId]);

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
