import { chooseNextPhysicsConcept, getConcept, missingRequirements } from './curriculum.js';
import { diagnoseReasoning, mergeDiagnosticCodes } from './diagnostics.js';
import { getInterventionPlan, getRemediationProblem } from './interventions.js';
import type { RemediationVerdict } from './interventions.js';
import { evaluateRemediation } from './remediation-evaluator.js';
import { LearningStore } from './store.js';
import type { EvidenceInput, InterventionRecord, MisconceptionRecord, ResumeState, ReviewRecord } from './store.js';

export type LearningStatus='new'|'diagnostic'|'learning';
export interface LearnerSnapshot{studentId:number;status:LearningStatus;currentConcept:string|null;nextConcept:string|null;mastery:Record<string,number>;missingRequirements:string[];activeMisconceptions:MisconceptionRecord[];interventionQueue:InterventionRecord[];dueReviews:ReviewRecord[];resume:ResumeState|undefined;}
export interface AttemptInput extends EvidenceInput{correct:boolean;misconceptionCodes?:string[];misconceptionSeverity?:number;}
export interface RemediationInput{reasoning:string;answer:string;correct:boolean;confidence?:number|null;hintUsed?:boolean;durationSeconds?:number|null;}
export interface RemediationResult{evaluation:ReturnType<typeof evaluateRemediation>;attemptId:number;snapshot:LearnerSnapshot;}

export class LearningEngine{
 constructor(private readonly store:LearningStore){}
 start(studentId:number):LearnerSnapshot{const existing=this.store.getSession(studentId);if(!existing)this.store.saveSession(studentId,'diagnostic',null,0);return this.snapshot(studentId);}
 snapshot(studentId:number):LearnerSnapshot{const session=this.store.getSession(studentId);const mastery=this.store.getMastery(studentId);const next=chooseNextPhysicsConcept(mastery);return{studentId,status:(session?.status??'new') as LearningStatus,currentConcept:session?.currentConcept??null,nextConcept:next?.id??null,mastery,missingRequirements:next?missingRequirements(mastery,next.id):[],activeMisconceptions:this.store.listMisconceptions(studentId).filter(m=>m.status==='active'),interventionQueue:this.store.listInterventions(studentId).filter(i=>i.status==='queued'||i.status==='active'),dueReviews:this.store.listDueReviews(studentId),resume:this.store.getResume(studentId)};}
 setCurrent(studentId:number,conceptId:string):void{getConcept(conceptId);const missing=missingRequirements(this.store.getMastery(studentId),conceptId);if(missing.length)throw new Error(`Cannot start ${conceptId}; requirements not yet demonstrated: ${missing.join(', ')}`);this.store.saveSession(studentId,'learning',conceptId,0);}
 recordAttempt(studentId:number,conceptId:string,correct:boolean,note=''):LearnerSnapshot{return this.recordStructuredAttempt(studentId,conceptId,{correct,note});}
 recordStructuredAttempt(studentId:number,conceptId:string,input:AttemptInput):LearnerSnapshot{
  getConcept(conceptId);const evidence:EvidenceInput={kind:'attempt',value:input.correct?1:0,...(input.note!==undefined?{note:input.note}:{}),...(input.lessonId!==undefined?{lessonId:input.lessonId}:{}),...(input.problemId!==undefined?{problemId:input.problemId}:{}),...(input.reasoning!==undefined?{reasoning:input.reasoning}:{}),...(input.confidence!==undefined?{confidence:input.confidence}:{}),...(input.hintUsed!==undefined?{hintUsed:input.hintUsed}:{}),...(input.durationSeconds!==undefined?{durationSeconds:input.durationSeconds}:{})};
  const evidenceId=this.store.addEvidence(studentId,conceptId,evidence);this.store.recordMastery(studentId,conceptId,input.correct);const findings=mergeDiagnosticCodes(conceptId,input.reasoning,input.misconceptionCodes,input.misconceptionSeverity??1);
  for(const finding of findings){const m=this.store.upsertMisconception(studentId,conceptId,finding.code,finding.severity,evidenceId);const plan=getInterventionPlan(finding);const first=plan?.problems.find(p=>p.stage==='discrimination');if(plan&&first)this.store.queueIntervention(studentId,m.id,conceptId,plan.prerequisiteConceptId,first.id,'discrimination',plan.strategy);}
  this.store.saveSession(studentId,'learning',conceptId,0);return this.snapshot(studentId);
 }
 diagnoseAttempt(conceptId:string,reasoning:string):ReturnType<typeof diagnoseReasoning>{return diagnoseReasoning(conceptId,reasoning);}
 getInterventionQueue(studentId:number):InterventionRecord[]{return this.store.listInterventions(studentId).filter(i=>i.status==='queued'||i.status==='active');}
 nextIntervention(studentId:number):InterventionRecord|undefined{const next=this.getInterventionQueue(studentId)[0];if(next?.status==='queued')this.store.activateIntervention(next.id);return next?this.store.getIntervention(next.id):undefined;}
 submitRemediationAttempt(studentId:number,interventionId:number,input:RemediationInput):RemediationResult{
  const intervention=this.store.getIntervention(interventionId);if(!intervention||intervention.studentId!==studentId)throw new Error('Unknown learner intervention');const problem=getRemediationProblem(intervention.problemId);if(problem.stage!==intervention.stage)throw new Error('Intervention stage does not match remediation problem');if(intervention.status==='queued')this.store.activateIntervention(interventionId);
  const evidenceId=this.store.addEvidence(studentId,problem.conceptId,{kind:'remediation_attempt',value:input.correct?1:0,problemId:problem.id,reasoning:input.reasoning,note:input.answer,confidence:input.confidence??null,hintUsed:input.hintUsed??false,durationSeconds:input.durationSeconds??null});
  const evaluation=evaluateRemediation(problem,input.reasoning,input.answer,input.correct);const attemptId=this.store.addRemediationAttempt(interventionId,evidenceId,evaluation.verdict,evaluation.checkpointScore);const m=this.store.listMisconceptions(studentId,problem.conceptId).find(x=>x.code===problem.misconceptionCode);
  if(m)this.store.recordMisconceptionSignal(m.id,evaluation.verdict as RemediationVerdict);
  if(evaluation.verdict==='repaired'&&intervention.stage==='discrimination'){
   const plan=getInterventionPlan({code:problem.misconceptionCode});const next=plan?.problems.find(p=>p.stage==='transfer');if(next)this.store.queueIntervention(studentId,intervention.misconceptionId,problem.conceptId,problem.prerequisiteConceptId,next.id,'transfer',plan!.strategy);this.store.completeIntervention(interventionId);
  }else if(evaluation.verdict==='repaired'&&intervention.stage==='transfer'){
   this.store.completeIntervention(interventionId);if(m){const state=this.store.getMisconceptionState(m.id);if(state&&state.positiveEvidence>=2&&state.confidence<=30)this.store.markMisconceptionRepaired(studentId,m.id);}this.store.scheduleReview(studentId,problem.conceptId,evaluation.checkpointScore);
  }
  if(evaluation.newMisconceptions.length){const all=diagnoseReasoning(problem.conceptId,input.reasoning);for(const code of evaluation.newMisconceptions){const finding=all.find(f=>f.code===code);const plan=finding&&getInterventionPlan(finding);if(finding&&plan){const first=plan.problems.find(p=>p.stage==='discrimination');if(first){const nm=this.store.upsertMisconception(studentId,problem.conceptId,code,finding.severity,evidenceId);this.store.queueIntervention(studentId,nm.id,problem.conceptId,plan.prerequisiteConceptId,first.id,'discrimination',plan.strategy);}}}}
  return{evaluation,attemptId,snapshot:this.snapshot(studentId)};
 }
 saveResume(studentId:number,lessonId:string|null,problemId:string|null,step:number,state:unknown=null):LearnerSnapshot{this.store.saveResume(studentId,lessonId,problemId,step,state);return this.snapshot(studentId);}
 resolveMisconception(studentId:number,misconceptionId:number):LearnerSnapshot{this.store.resolveMisconception(studentId,misconceptionId);return this.snapshot(studentId);}
 placeByDemonstratedMastery(studentId:number,scores:Record<string,number>):LearnerSnapshot{for(const[conceptId,score]of Object.entries(scores)){getConcept(conceptId);this.store.setMastery(studentId,conceptId,score);this.store.addEvidence(studentId,conceptId,'placement',score,'Demonstrated ability placement');}this.store.saveSession(studentId,'learning',null,0);return this.snapshot(studentId);}
}
