import type { EvidenceInput, InterventionRecord, MisconceptionRecord, MisconceptionState, ResumeState, ReviewRecord } from './store-types.js';

export interface AtomicRemediationInput {
  studentId: number; interventionId: number; interventionMisconceptionId: number; conceptId: string; problemId: string;
  evidence: EvidenceInput; verdict: string; checkpointScore: number; correct: boolean;
  signalMisconceptionId: number | null; signalVerdict: string; completeIntervention: boolean; resolveMisconception: boolean;
  transfer?: { problemId: string; prerequisiteConceptId: string; strategy: string } | undefined;
  reviewScore?: number | undefined; reviewAt?: Date | undefined;
}

export interface AtomicReviewInput {
  studentId: number; conceptId: string; problemId: string; evidence: EvidenceInput;
  outcome: string; checkpointScore: number; correct: boolean; misconceptionId: number | null;
  misconceptionVerdict: string; referenceTime: Date;
}

export interface LearningStoreContract {
  close(): Promise<void>; getSession(studentId: number): Promise<{status:string; currentConcept:string|null; diagnosticIndex:number; updatedAt:string}|undefined>;
  saveSession(studentId:number,status:string,currentConcept:string|null,diagnosticIndex?:number): Promise<void>; ensureStudent(nickname:string): Promise<number>;
  getMastery(studentId:number): Promise<Record<string,number>>; setMastery(studentId:number,conceptId:string,score:number): Promise<void>; recordMastery(studentId:number,conceptId:string,correct:boolean): Promise<void>;
  addEvidence(studentId:number,conceptId:string,input:EvidenceInput): Promise<number>; recordAttemptEvidenceAndMastery?(studentId:number,conceptId:string,input:EvidenceInput,correct:boolean): Promise<number>;
  recordRemediationOutcomeAtomic?(input:AtomicRemediationInput): Promise<number>; recordReviewOutcomeAtomic?(input:AtomicReviewInput): Promise<number>;
  upsertMisconception(studentId:number,conceptId:string,code:string,severity:number,evidenceId:number): Promise<MisconceptionRecord>; listMisconceptions(studentId:number,conceptId?:string): Promise<MisconceptionRecord[]>;
  getMisconceptionState(id:number): Promise<MisconceptionState|undefined>; recordMisconceptionSignal(id:number,verdict:string): Promise<MisconceptionState>; markMisconceptionRepaired(studentId:number,id:number): Promise<void>;
  queueIntervention(studentId:number,misconceptionId:number,conceptId:string,prerequisiteConceptId:string,problemId:string,stage:'discrimination'|'transfer',strategy:string): Promise<InterventionRecord>;
  getIntervention(id:number): Promise<InterventionRecord|undefined>; listInterventions(studentId:number,status?:string): Promise<InterventionRecord[]>; activateIntervention(id:number): Promise<void>; completeIntervention(id:number): Promise<void>;
  addRemediationAttempt(interventionId:number,evidenceId:number,verdict:string,checkpointScore:number): Promise<number>; scheduleReview(studentId:number,conceptId:string,score:number,referenceTime?:Date): Promise<ReviewRecord>; listDueReviews(studentId:number,when?:string): Promise<ReviewRecord[]>;
  addReviewAttempt(studentId:number,conceptId:string,problemId:string,evidenceId:number,outcome:string,checkpointScore:number): Promise<number>; resolveMisconception(studentId:number,id:number): Promise<void>;
  saveResume(studentId:number,lessonId:string|null,problemId:string|null,step:number,state?:unknown): Promise<void>; getResume(studentId:number): Promise<ResumeState|undefined>;
}
