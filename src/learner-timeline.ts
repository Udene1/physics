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

/** Reconstructs the learner's durable learning loop from relational state. */
export function getLearnerTimeline(store: LearningStore, studentId: number): LearnerTimelineEvent[] {
  const evidence = store.db.prepare(`SELECT id, created_at AS at, concept_id, problem_id, kind, note, value FROM evidence WHERE student_id=?`).all(studentId) as Row[];
  const remediation = store.db.prepare(`SELECT ra.id, ra.created_at AS at, e.concept_id, e.problem_id, ra.verdict, ra.checkpoint_score FROM remediation_attempts ra JOIN evidence e ON e.id=ra.evidence_id JOIN interventions i ON i.id=ra.intervention_id WHERE i.student_id=?`).all(studentId) as Row[];
  const reviews = store.db.prepare(`SELECT id, created_at AS at, concept_id, problem_id, outcome, checkpoint_score FROM review_attempts WHERE student_id=?`).all(studentId) as Row[];
  const interventions = store.db.prepare(`SELECT id, created_at AS at, concept_id, problem_id, stage, status FROM interventions WHERE student_id=?`).all(studentId) as Row[];

  const events: LearnerTimelineEvent[] = [
    ...evidence.map(row => ({
      id:`evidence:${String(row.id)}`, type:'evidence' as const, at:String(row.at), conceptId:String(row.concept_id),
      problemId:row.problem_id===null?null:String(row.problem_id),
      summary:`${String(row.kind)}${row.note?`: ${String(row.note)}`:''}`, verdict:null,
      score:row.value===null?null:Number(row.value),
    })),
    ...remediation.map(row => ({
      id:`remediation:${String(row.id)}`, type:'remediation' as const, at:String(row.at), conceptId:String(row.concept_id),
      problemId:row.problem_id===null?null:String(row.problem_id), summary:`Remediation ${String(row.verdict)}`,
      verdict:String(row.verdict), score:Number(row.checkpoint_score),
    })),
    ...reviews.map(row => ({
      id:`review:${String(row.id)}`, type:'review' as const, at:String(row.at), conceptId:String(row.concept_id),
      problemId:row.problem_id===null?null:String(row.problem_id), summary:`Review ${String(row.outcome)}`,
      verdict:String(row.outcome), score:Number(row.checkpoint_score),
    })),
    ...interventions.map(row => ({
      id:`intervention:${String(row.id)}`, type:'intervention' as const, at:String(row.at), conceptId:String(row.concept_id),
      problemId:row.problem_id===null?null:String(row.problem_id), summary:`Intervention ${String(row.stage)} (${String(row.status)})`,
      verdict:String(row.status), score:null,
    })),
  ];
  return events.sort((a,b)=>a.at.localeCompare(b.at)||a.id.localeCompare(b.id));
}
