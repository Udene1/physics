import type { LearningStoreContract } from '../store-contract.js';
import type { LearnerTimelineEvent } from '../learner-timeline.js';

type Row=Record<string,unknown>;
export async function getPostgresLearnerTimeline(store:LearningStoreContract&{query(sql:string,params?:unknown[]):Promise<{rows:Row[]}>},studentId:number):Promise<LearnerTimelineEvent[]>{
 const [e,r,v,i]=await Promise.all([
  store.query('SELECT id,created_at AS at,concept_id,problem_id,kind,note,value FROM evidence WHERE student_id=$1',[studentId]),
  store.query('SELECT ra.id,ra.created_at AS at,e.concept_id,e.problem_id,ra.verdict,ra.checkpoint_score FROM remediation_attempts ra JOIN evidence e ON e.id=ra.evidence_id JOIN interventions i ON i.id=ra.intervention_id WHERE i.student_id=$1',[studentId]),
  store.query('SELECT id,created_at AS at,concept_id,problem_id,outcome,checkpoint_score FROM review_attempts WHERE student_id=$1',[studentId]),
  store.query('SELECT id,created_at AS at,concept_id,problem_id,stage,status FROM interventions WHERE student_id=$1',[studentId])
 ]);
 const events:LearnerTimelineEvent[]=[...e.rows.map(x=>({id:`evidence:${x.id}`,type:'evidence' as const,at:String(x.at),conceptId:String(x.concept_id),problemId:x.problem_id==null?null:String(x.problem_id),summary:`${x.kind}${x.note?`: ${x.note}`:''}`,verdict:null,score:x.value==null?null:Number(x.value)})),...r.rows.map(x=>({id:`remediation:${x.id}`,type:'remediation' as const,at:String(x.at),conceptId:String(x.concept_id),problemId:x.problem_id==null?null:String(x.problem_id),summary:`Remediation ${x.verdict}`,verdict:String(x.verdict),score:Number(x.checkpoint_score)})),...v.rows.map(x=>({id:`review:${x.id}`,type:'review' as const,at:String(x.at),conceptId:String(x.concept_id),problemId:x.problem_id==null?null:String(x.problem_id),summary:`Review ${x.outcome}`,verdict:String(x.outcome),score:Number(x.checkpoint_score)})),...i.rows.map(x=>({id:`intervention:${x.id}`,type:'intervention' as const,at:String(x.at),conceptId:String(x.concept_id),problemId:x.problem_id==null?null:String(x.problem_id),summary:`Intervention ${x.stage} (${x.status})`,verdict:String(x.status),score:null}))];return events.sort((a,b)=>a.at.localeCompare(b.at)||a.id.localeCompare(b.id));
}
