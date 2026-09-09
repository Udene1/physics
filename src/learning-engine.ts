import { chooseNextPhysicsConcept, getConcept, missingRequirements } from './curriculum.js';
import { LearningStore } from './store.js';
import type { EvidenceInput, MisconceptionRecord, ResumeState } from './store.js';

export type LearningStatus = 'new' | 'diagnostic' | 'learning';
export interface LearnerSnapshot { studentId:number; status:LearningStatus; currentConcept:string|null; nextConcept:string|null; mastery:Record<string,number>; missingRequirements:string[]; activeMisconceptions:MisconceptionRecord[]; resume:ResumeState|undefined; }
export interface AttemptInput extends EvidenceInput { correct:boolean; misconceptionCodes?:string[]; misconceptionSeverity?:number; }

export class LearningEngine {
  constructor(private readonly store: LearningStore) {}
  start(studentId:number): LearnerSnapshot {
    const existing = this.store.getSession(studentId);
    if (!existing) this.store.saveSession(studentId, 'diagnostic', null, 0);
    return this.snapshot(studentId);
  }
  snapshot(studentId:number): LearnerSnapshot {
    const session = this.store.getSession(studentId);
    const mastery = this.store.getMastery(studentId);
    const next = chooseNextPhysicsConcept(mastery);
    const current = session?.currentConcept ?? null;
    return { studentId, status:(session?.status ?? 'new') as LearningStatus, currentConcept:current, nextConcept:next?.id ?? null, mastery, missingRequirements:next ? missingRequirements(mastery,next.id) : [], activeMisconceptions:this.store.listMisconceptions(studentId).filter(m => m.status === 'active'), resume:this.store.getResume(studentId) };
  }
  setCurrent(studentId:number, conceptId:string): void {
    getConcept(conceptId);
    const mastery = this.store.getMastery(studentId);
    const missing = missingRequirements(mastery, conceptId);
    if (missing.length) throw new Error(`Cannot start ${conceptId}; requirements not yet demonstrated: ${missing.join(', ')}`);
    this.store.saveSession(studentId, 'learning', conceptId, 0);
  }
  recordAttempt(studentId:number, conceptId:string, correct:boolean, note=''): LearnerSnapshot {
    return this.recordStructuredAttempt(studentId, conceptId, {correct,note});
  }
  recordStructuredAttempt(studentId:number, conceptId:string, input:AttemptInput): LearnerSnapshot {
    getConcept(conceptId);
    const evidence: EvidenceInput = {
      kind:'attempt', value:input.correct ? 1 : 0,
      ...(input.note !== undefined ? {note:input.note} : {}),
      ...(input.lessonId !== undefined ? {lessonId:input.lessonId} : {}),
      ...(input.problemId !== undefined ? {problemId:input.problemId} : {}),
      ...(input.reasoning !== undefined ? {reasoning:input.reasoning} : {}),
      ...(input.confidence !== undefined ? {confidence:input.confidence} : {}),
      ...(input.hintUsed !== undefined ? {hintUsed:input.hintUsed} : {}),
      ...(input.durationSeconds !== undefined ? {durationSeconds:input.durationSeconds} : {}),
    };
    const evidenceId = this.store.addEvidence(studentId, conceptId, evidence);
    this.store.recordMastery(studentId, conceptId, input.correct);
    for (const code of input.misconceptionCodes ?? []) this.store.upsertMisconception(studentId, conceptId, code, input.misconceptionSeverity ?? 1, evidenceId);
    this.store.saveSession(studentId, 'learning', conceptId, 0);
    return this.snapshot(studentId);
  }
  saveResume(studentId:number, lessonId:string|null, problemId:string|null, step:number, state:unknown = null): LearnerSnapshot {
    this.store.saveResume(studentId,lessonId,problemId,step,state);
    return this.snapshot(studentId);
  }
  resolveMisconception(studentId:number, misconceptionId:number): LearnerSnapshot {
    this.store.resolveMisconception(studentId,misconceptionId);
    return this.snapshot(studentId);
  }
  placeByDemonstratedMastery(studentId:number, scores:Record<string,number>): LearnerSnapshot {
    for (const [conceptId,score] of Object.entries(scores)) { getConcept(conceptId); this.store.setMastery(studentId, conceptId, score); this.store.addEvidence(studentId, conceptId, 'placement', score, 'Demonstrated ability placement'); }
    this.store.saveSession(studentId, 'learning', null, 0);
    return this.snapshot(studentId);
  }
}
