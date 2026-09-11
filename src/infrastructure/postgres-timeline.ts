import type { LearningStoreContract } from '../store-contract.js';
import type { LearnerTimelineEvent } from '../learner-timeline.js';

type Row=Record<string,unknown>;
export async function getPostgresLearnerTimeline(store:LearningStoreContract&{query(sql:string,params?:unknown[]):Promise<{rows:Row[]}>},studentId:number):Promise<LearnerTimelineEvent[]>{
 const result=await store.query(`SELECT id,created_at,event_type,aggregate_type,concept_id,payload FROM learning_events WHERE student_id=$1 ORDER BY id`,[studentId]);
 return result.rows.map(x=>{
  const payload=(x.payload&&typeof x.payload==='object'?x.payload:{}) as Record<string,unknown>;
  const eventType=String(x.event_type);const aggregate=String(x.aggregate_type);const conceptId=x.concept_id==null?null:String(x.concept_id);
  const problemId=payload.problemId==null?null:String(payload.problemId);
  const score=payload.checkpointScore==null?(payload.value==null?null:Number(payload.value)):Number(payload.checkpointScore);
  if(eventType==='evidence.recorded')return{id:`event:${x.id}`,type:'evidence' as const,at:String(x.created_at),conceptId,problemId,summary:`Evidence ${payload.kind??'recorded'}`,verdict:null,score};
  if(eventType==='remediation.attempted')return{id:`event:${x.id}`,type:'remediation' as const,at:String(x.created_at),conceptId,problemId,summary:`Remediation ${payload.verdict??'attempted'}`,verdict:payload.verdict==null?null:String(payload.verdict),score};
  if(eventType==='review.attempted')return{id:`event:${x.id}`,type:'review' as const,at:String(x.created_at),conceptId,problemId,summary:`Review ${payload.outcome??'attempted'}`,verdict:payload.outcome==null?null:String(payload.outcome),score};
  return{id:`event:${x.id}`,type:'artifact' as const,at:String(x.created_at),conceptId,problemId,summary:`Learning artifact ${eventType.replace('learning_artifact_','')}`,verdict:null,score};
 });
}
