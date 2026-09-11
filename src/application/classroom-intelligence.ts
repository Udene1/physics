import type { Pool } from 'pg';

export interface ClassroomIntelligence {
  classroomId: number; name: string; code: string; students: number;
  mastery: Array<{ conceptId: string; averageScore: number; learnersAttempted: number }>;
  misconceptions: Array<{ code: string; conceptId: string; affectedLearners: number; totalOccurrences: number; averageConfidence: number }>;
  interventionEffectiveness: { attempts: number; repaired: number; stillPresent: number; newMisconception: number; insufficientEvidence: number; repairRate: number | null };
  strategyEffectiveness: Array<{ strategy: string; attempts: number; repaired: number; repairRate: number | null }>;
  attention: Array<{ studentId: number; attention: 'high' | 'medium'; reasons: string[]; activeMisconceptions: number; dueReviews: number }>;
  readyToAdvance: number[];
  bottlenecks: Array<{ conceptId: string; affectedLearners: number; averageMastery: number; reason: string }>;
}
const number = (value: unknown) => Number(value ?? 0);

export async function getClassroomIntelligence(pool: Pool, classroomId: number): Promise<ClassroomIntelligence> {
  const classroom = await pool.query('SELECT id,name,code FROM classrooms WHERE id=$1', [classroomId]);
  if (classroom.rowCount !== 1) throw new Error('Unknown classroom');
  const [roster, mastery, misconceptions, remediation, attention, strategies, readiness] = await Promise.all([
    pool.query('SELECT student_id FROM classroom_students WHERE classroom_id=$1 ORDER BY student_id', [classroomId]),
    pool.query(`SELECT m.concept_id, AVG(m.score)::double precision AS average_score, COUNT(*) FILTER (WHERE m.attempts > 0)::int AS learners_attempted
      FROM classroom_students cs JOIN mastery m ON m.student_id=cs.student_id WHERE cs.classroom_id=$1 GROUP BY m.concept_id ORDER BY m.concept_id`, [classroomId]),
    pool.query(`SELECT m.code, m.concept_id, COUNT(DISTINCT m.student_id)::int AS affected_learners, SUM(m.occurrences)::int AS total_occurrences, AVG(COALESCE(ms.confidence,0))::double precision AS average_confidence
      FROM classroom_students cs JOIN misconceptions m ON m.student_id=cs.student_id LEFT JOIN misconception_state ms ON ms.misconception_id=m.id
      WHERE cs.classroom_id=$1 AND m.status='active' GROUP BY m.code,m.concept_id ORDER BY affected_learners DESC,total_occurrences DESC`, [classroomId]),
    pool.query(`SELECT ra.verdict, COUNT(*)::int AS count FROM classroom_students cs JOIN interventions i ON i.student_id=cs.student_id JOIN remediation_attempts ra ON ra.intervention_id=i.id WHERE cs.classroom_id=$1 GROUP BY ra.verdict`, [classroomId]),
    pool.query(`SELECT cs.student_id, COUNT(DISTINCT m.id) FILTER (WHERE m.status='active')::int AS active_misconceptions, COUNT(DISTINCT cr.concept_id) FILTER (WHERE cr.due_at<=now())::int AS due_reviews,
      MAX(m.severity) FILTER (WHERE m.status='active')::int AS max_severity, MAX(COALESCE(ms.confidence,0)) FILTER (WHERE m.status='active')::int AS max_confidence, MAX(m.occurrences) FILTER (WHERE m.status='active')::int AS max_occurrences
      FROM classroom_students cs LEFT JOIN misconceptions m ON m.student_id=cs.student_id LEFT JOIN misconception_state ms ON ms.misconception_id=m.id LEFT JOIN concept_reviews cr ON cr.student_id=cs.student_id
      WHERE cs.classroom_id=$1 GROUP BY cs.student_id ORDER BY max_confidence DESC NULLS LAST,max_severity DESC NULLS LAST,cs.student_id`, [classroomId]),
    pool.query(`SELECT i.strategy, COUNT(*)::int AS attempts, COUNT(*) FILTER (WHERE ra.verdict='repaired')::int AS repaired
      FROM classroom_students cs JOIN interventions i ON i.student_id=cs.student_id JOIN remediation_attempts ra ON ra.intervention_id=i.id
      WHERE cs.classroom_id=$1 GROUP BY i.strategy ORDER BY attempts DESC,repaired DESC`, [classroomId]),
    pool.query(`SELECT cs.student_id FROM classroom_students cs
      JOIN mastery m ON m.student_id=cs.student_id
      WHERE cs.classroom_id=$1 AND m.score>=80 AND m.attempts>0
      GROUP BY cs.student_id
      HAVING COUNT(*) FILTER (WHERE m.score>=80) = COUNT(*) AND NOT EXISTS
        (SELECT 1 FROM misconceptions mx WHERE mx.student_id=cs.student_id AND mx.status='active')
      ORDER BY cs.student_id`, [classroomId]),
  ]);
  const outcomeCounts = new Map<string, number>(remediation.rows.map((r) => [String(r.verdict), number(r.count)]));
  const repaired = number(outcomeCounts.get('repaired')), stillPresent = number(outcomeCounts.get('still_present')), newMisconception = number(outcomeCounts.get('new_misconception')), insufficientEvidence = number(outcomeCounts.get('insufficient_evidence'));
  const attempts = remediation.rows.reduce((sum, row) => sum + number(row.count), 0);
  const totalStudents = roster.rowCount ?? 0;
  const bottlenecks = mastery.rows.map((r) => ({ conceptId: String(r.concept_id), affectedLearners: number(r.attempted), averageMastery: number(r.average_score), reason: '' })).map((r) => ({ ...r, affectedLearners: number(r.affectedLearners), reason: r.averageMastery < 60 ? 'class mastery is below 60%' : r.affectedLearners < totalStudents * 0.5 ? 'fewer than half the class has demonstrated evidence' : '' })).filter((r) => r.reason);
  return {
    classroomId, name: String(classroom.rows[0].name), code: String(classroom.rows[0].code), students: totalStudents,
    mastery: mastery.rows.map((r) => ({ conceptId: String(r.concept_id), averageScore: number(r.average_score), learnersAttempted: number(r.learners_attempted) })),
    misconceptions: misconceptions.rows.map((r) => ({ code: String(r.code), conceptId: String(r.concept_id), affectedLearners: number(r.affected_learners), totalOccurrences: number(r.total_occurrences), averageConfidence: number(r.average_confidence) })),
    interventionEffectiveness: { attempts, repaired, stillPresent, newMisconception, insufficientEvidence, repairRate: attempts === 0 ? null : repaired / attempts },
    strategyEffectiveness: strategies.rows.map((r) => { const n = number(r.attempts); const repairedForStrategy = number(r.repaired); return { strategy: String(r.strategy), attempts: n, repaired: repairedForStrategy, repairRate: n === 0 ? null : repairedForStrategy / n }; }),
    attention: attention.rows.map((r) => { const reasons: string[] = []; if (number(r.max_confidence) >= 60 || number(r.max_severity) >= 4) reasons.push('high-confidence or high-severity misconception'); if (number(r.max_occurrences) >= 3) reasons.push('recurring reasoning pattern'); if (number(r.due_reviews) >= 2) reasons.push('multiple reviews due'); return { studentId: number(r.student_id), attention: reasons.length >= 2 ? 'high' as const : 'medium' as const, reasons, activeMisconceptions: number(r.active_misconceptions), dueReviews: number(r.due_reviews) }; }).filter((r) => r.reasons.length > 0),
    readyToAdvance: readiness.rows.map((r) => number(r.student_id)),
    bottlenecks,
  };
}
export async function createClassroom(pool: Pool, name: string, code: string): Promise<number> { const result = await pool.query('INSERT INTO classrooms(name,code) VALUES($1,$2) RETURNING id', [name.trim(), code.trim().toUpperCase()]); return Number(result.rows[0].id); }
export async function enrollStudent(pool: Pool, classroomId: number, studentId: number): Promise<void> { await pool.query('INSERT INTO classroom_students(classroom_id,student_id) VALUES($1,$2) ON CONFLICT(classroom_id,student_id) DO NOTHING', [classroomId,studentId]); }
