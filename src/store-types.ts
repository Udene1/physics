export interface MasteryRecord { studentId:number; conceptId:string; score:number; attempts:number; correct:number; updatedAt:string; }
export interface EvidenceInput { kind:string; value?:number|null; note?:string; lessonId?:string|null; problemId?:string|null; reasoning?:string|null; confidence?:number|null; hintUsed?:boolean; durationSeconds?:number|null; }
export interface MisconceptionRecord { id:number; studentId:number; conceptId:string; code:string; severity:number; status:'active'|'resolved'; occurrences:number; lastEvidenceId:number|null; updatedAt:string; }
export interface MisconceptionState { misconceptionId:number; confidence:number; positiveEvidence:number; negativeEvidence:number; lastVerdict:string|null; updatedAt:string; }
export interface InterventionRecord { id:number; studentId:number; misconceptionId:number; conceptId:string; prerequisiteConceptId:string; problemId:string; stage:'discrimination'|'transfer'; strategy:string; status:'queued'|'active'|'completed'|'blocked'; createdAt:string; updatedAt:string; }
export interface RemediationAttempt { id:number; interventionId:number; evidenceId:number; verdict:string; checkpointScore:number; createdAt:string; }
export interface ReviewRecord { studentId:number; conceptId:string; dueAt:string; intervalDays:number; streak:number; lastScore:number; updatedAt:string; }
export interface ReviewAttempt { id:number; studentId:number; conceptId:string; problemId:string; evidenceId:number; outcome:string; checkpointScore:number; createdAt:string; }
export interface ResumeState { lessonId:string|null; problemId:string|null; step:number; stateJson:string|null; updatedAt:string; }
