import type { MasteryRecord, MisconceptionRecord, ProblemAttemptRecord, ResumeState, ReviewRecord } from './store.js';
import type { ReasoningSignal } from './reasoning.js';

export type ModernSpecialization='relativity'|'quantum'|'atomic_nuclear';
export interface EvidenceRecord{id:number;studentId:number;conceptId:string;kind:string;value:number|null;note:string;createdAt:string;}
export interface LearningRepository{
 ensureStudent(nickname:string):number;
 getMastery(studentId:number):Record<string,number>;
 recordMastery(studentId:number,conceptId:string,correct:boolean):MasteryRecord;
 setMastery(studentId:number,conceptId:string,score:number):void;
 saveSession(studentId:number,status:string,currentConcept:string|null,diagnosticIndex:number):void;
 getSession(studentId:number):{status:string;currentConcept:string|null;diagnosticIndex:number}|undefined;
 addEvidence(studentId:number,conceptId:string,kind:string,value:number|null,note:string):void;
 listEvidence(studentId:number,conceptId?:string):EvidenceRecord[];
 addMisconception(studentId:number,conceptId:string,code:string,note:string):MisconceptionRecord;
 getMisconception(id:number):MisconceptionRecord|undefined;
 listOpenMisconceptions(studentId:number,conceptId?:string):MisconceptionRecord[];
 resolveMisconception(id:number):void;
 saveResume(studentId:number,lessonId:string,problemId:string|null,step:number):void;
 getResume(studentId:number):ResumeState|undefined;
 scheduleReview(studentId:number,conceptId:string,correct:boolean):ReviewRecord;
 getDueReviews(studentId:number,now?:string):ReviewRecord[];
 recordProblemAttempt(studentId:number,problemId:string,conceptId:string,answer:string,correct:boolean,reasoning:string,confidence:number|null,reasoningSignals?:ReasoningSignal[],misconceptionCodes?:string[]):ProblemAttemptRecord;
 listProblemAttempts(studentId:number,problemId?:string):ProblemAttemptRecord[];
 setModernSpecialization(studentId:number,specialization:ModernSpecialization):void;
 getModernSpecialization(studentId:number):ModernSpecialization|undefined;
 transaction<T>(work:()=>T):T;
}
