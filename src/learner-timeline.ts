import type { LearningStore } from './store.js';

export type LearnerTimelineEvent = {
  id: string;
  type: 'evidence' | 'remediation' | 'review' | 'intervention';
  at: string;
  conceptId: string;
  problemId: string | null;
  summary: string;
  verdict: string | null;
  score: number | null;
};

type Row = Record<string, unknown>;

/** Reconstructs the learner's durable learning loop from SQLite state. */
export function getLearnerTimeline(store: LearningStore, studentId: number): LearnerTimelineEvent[] {
  const rows = store.db.prepare(`
    SELECT 'evidence' AS type, id, created_at AS at, concept_id, problem_id,
           kind || CASE WHEN note IS NOT NULL AND note <> '' THEN ': ' || note ELSE '' END AS summary,
           NULL AS verdict, value AS score
    FROM evidence WHERE student_id = ?
    UNION ALL
    SELECT 'remediation', ra.id, ra.created_at, e.concept_id, e.problem_id,
           'Remediation ' || ra.verdict, ra.verdict, ra.checkpoint_score
    FROM remediation_attempts ra
    JOIN evidence e ON e.id = ra.evidence_id
    JOIN interventions i ON i.id = ra.intervention_id
    WHERE i.student_id = ?
    UNION ALL
    SELECT 'review', ra.id, ra.created_at, ra.concept_id, ra.problem_id,
           'Review ' || ra.outcome, ra.outcome, ra.checkpoint_score
    FROM review_attempts ra WHERE ra.student_id = ?
    UNION ALL
    SELECT 'intervention', i.id, i.created_at, i.concept_id, i.problem_id,
           'Intervention ' || i.stage || ' (' || i.status || ')', i.status, NULL
    FROM interventions i WHERE i.student_id = ?
    ORDER BY at, id
  `).all(studentId, studentId, studentId, studentId) as Row[];

  return rows.map(row => ({
    id: `${String(row.type)}:${String(row.id)}`,
    type: row.type as LearnerTimelineEvent['type'],
    at: String(row.at),
    conceptId: String(row.concept_id),
    problemId: row.problem_id === null ? null : String(row.problem_id),
    summary: String(row.summary),
    verdict: row.verdict === null ? null : String(row.verdict),
    score: row.score === null ? null : Number(row.score),
  }));
}
