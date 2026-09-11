import type { LearningStore } from './store.js';

type Row=Record<string,unknown>;
export type LearnerTimelineEvent={id:string;type:'evidence'|'remediation'|'review'|'intervention'|'artifact';at:string;conceptId:string|null;problemId:string|null;summary:string;verdict:string|null;score:number|null};

/** Legacy SQLite timeline retained only for the transitional LearningEngine. */
export function getLearnerTimeline(store:LearningStore,studentId:number):LearnerTimelineEvent[]{
  const events:LearnerTimelineEvent[]=[];
  const evidence=store.db.prepare('SELECT id,created_at,concept_id,problem_id,kind,note,value FROM evidence WHERE student_id=?').all(studentId) as Row[];
  for(const x of evidence)events.push({id:`evidence:${x.id}`,type:'evidence',at:String(x.created_at),conceptId:String(x.concept_id),problemId:x.problem_id==null?null:String(x.problem_id),summary:`${x.kind}${x.note?`: ${x.note}`:''}`,verdict:null,score:x.value==null?null:Number(x.value)});
  const interventions=store.db.prepare('SELECT id,created_at,concept_id,problem_id,stage,status FROM interventions WHERE student_id=?').all(studentId) as Row[];
  for(const x of interventions)events.push({id:`intervention:${x.id}`,type:'intervention',at:String(x.created_at),conceptId:String(x.concept_id),problemId:String(x.problem_id),summary:`Intervention ${x.stage} (${x.status})`,verdict:String(x.status),score:null});
  const remediation=store.db.prepare(`SELECT ra.id,ra.created_at,e.concept_id,e.problem_id,ra.verdict,ra.checkpoint_score FROM remediation_attempts ra JOIN evidence e ON e.id=ra.evidence_id JOIN interventions i ON i.id=ra.intervention_id WHERE i.student_id=?`).all(studentId) as Row[];
  for(const x of remediation)events.push({id:`remediation:${x.id}`,type:'remediation',at:String(x.created_at),conceptId:String(x.concept_id),problemId:x.problem_id==null?null:String(x.problem_id),summary:`Remediation ${x.verdict}`,verdict:String(x.verdict),score:Number(x.checkpoint_score)});
  const reviews=store.db.prepare('SELECT id,created_at,concept_id,problem_id,outcome,checkpoint_score FROM review_attempts WHERE student_id=?').all(studentId) as Row[];
  for(const x of reviews)events.push({id:`review:${x.id}`,type:'review',at:String(x.created_at),conceptId:String(x.concept_id),problemId:String(x.problem_id),summary:`Review ${x.outcome}`,verdict:String(x.outcome),score:Number(x.checkpoint_score)});
  return events.sort((a,b)=>a.at.localeCompare(b.at)||a.id.localeCompare(b.id));
}
