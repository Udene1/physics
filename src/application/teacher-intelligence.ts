import type { PostgresLearningStore } from '../infrastructure/postgres-store.js';

export interface TeacherLearnerSummary {
  studentId: number;
  mastery: Array<{ conceptId: string; score: number; attempts: number; correct: number }>;
  activeMisconceptions: Array<{ code: string; conceptId: string; severity: number; occurrences: number; confidence: number; positiveEvidence: number; negativeEvidence: number }>;
  interventions: { queued: number; active: number; completed: number };
  dueReviews: number;
  recentEvidence: Array<{ conceptId: string; kind: string; value: number | null; problemId: string | null; createdAt: string }>;
  attention: 'high' | 'medium' | 'low';
  attentionReasons: string[];
}

export async function getTeacherLearnerSummary(store: PostgresLearningStore, studentId: number): Promise<TeacherLearnerSummary> {
  const [mastery, misconceptions, interventions, reviews, evidence] = await Promise.all([
    store.query('SELECT concept_id, score, attempts, correct FROM mastery WHERE student_id=$1 ORDER BY score ASC, concept_id', [studentId]),
    store.query(`SELECT m.code, m.concept_id, m.severity, m.occurrences,
      COALESCE(s.confidence,0) AS confidence, COALESCE(s.positive_evidence,0) AS positive_evidence,
      COALESCE(s.negative_evidence,0) AS negative_evidence
      FROM misconceptions m LEFT JOIN misconception_state s ON s.misconception_id=m.id
      WHERE m.student_id=$1 AND m.status='active' ORDER BY m.severity DESC, COALESCE(s.confidence,0) DESC`, [studentId]),
    store.query(`SELECT status, count(*)::int AS count FROM interventions
      WHERE student_id=$1 AND status IN ('queued','active','completed') GROUP BY status`, [studentId]),
    store.query('SELECT count(*)::int AS count FROM concept_reviews WHERE student_id=$1 AND due_at<=now()', [studentId]),
    store.query(`SELECT concept_id, kind, value, problem_id, created_at
      FROM evidence WHERE student_id=$1 ORDER BY created_at DESC LIMIT 20`, [studentId]),
  ]);

  const activeMisconceptions = misconceptions.rows.map((r) => ({
    code: String(r.code), conceptId: String(r.concept_id), severity: Number(r.severity), occurrences: Number(r.occurrences),
    confidence: Number(r.confidence), positiveEvidence: Number(r.positive_evidence), negativeEvidence: Number(r.negative_evidence),
  }));
  const reasons: string[] = [];
  if (activeMisconceptions.some((m) => m.severity >= 4 || m.confidence >= 60)) reasons.push('A high-confidence or high-severity misconception is active.');
  if (activeMisconceptions.some((m) => m.occurrences >= 3)) reasons.push('The same reasoning pattern has recurred across attempts.');
  const dueReviews = Number(reviews.rows[0]?.count ?? 0);
  if (dueReviews >= 3) reasons.push('Several concept reviews are due.');
  const attention: TeacherLearnerSummary['attention'] = reasons.length >= 2 ? 'high' : reasons.length === 1 ? 'medium' : 'low';
  const counts = { queued: 0, active: 0, completed: 0 };
  for (const row of interventions.rows) {
    const status = String(row.status) as keyof typeof counts;
    if (status in counts) counts[status] = Number(row.count);
  }
  return {
    studentId,
    mastery: mastery.rows.map((r) => ({ conceptId: String(r.concept_id), score: Number(r.score), attempts: Number(r.attempts), correct: Number(r.correct) })),
    activeMisconceptions,
    interventions: counts,
    dueReviews,
    recentEvidence: evidence.rows.map((r) => ({ conceptId: String(r.concept_id), kind: String(r.kind), value: r.value == null ? null : Number(r.value), problemId: r.problem_id == null ? null : String(r.problem_id), createdAt: new Date(String(r.created_at)).toISOString() })),
    attention,
    attentionReasons: reasons,
  };
}
