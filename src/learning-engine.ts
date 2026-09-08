import { chooseNextPhysicsConcept, CURRICULUM, getConcept, missingRequirements } from './curriculum.js';
import { LearningStore, MisconceptionRecord, ReviewRecord, ResumeState } from './store.js';

export type LearningStatus = 'new' | 'diagnostic' | 'learning';
export type JourneyStatus = 'locked' | 'available' | 'learning' | 'mastered';
export interface JourneyNode { id:string; name:string; domain:string; status:JourneyStatus; mastery:number; prerequisites:string[]; mathDependencies:string[]; }
export interface LearnerSnapshot { studentId:number; status:LearningStatus; currentConcept:string|null; nextConcept:string|null; mastery:Record<string,number>; missingRequirements:string[]; openMisconceptions:number; resume:ResumeState|undefined; dueReviews:ReviewRecord[]; journey:JourneyNode[]; }

export class LearningEngine {
  constructor(private readonly store: LearningStore) {}
  start(studentId:number): LearnerSnapshot {
    const existing = this.store.getSession(studentId);
    if (!existing) this.store.saveSession(studentId, 'diagnostic', null, 0);
    return this.snapshot(studentId);
  }
  journey(studentId:number): JourneyNode[] {
    const mastery = this.store.getMastery(studentId);
    return CURRICULUM.map(concept => {
      const score = mastery[concept.id] ?? 0;
      const requirements = missingRequirements(mastery,concept.id);
      const status:JourneyStatus = score >= 100 ? 'mastered' : requirements.length ? 'locked' : score > 0 ? 'learning' : 'available';
      return {id:concept.id,name:concept.name,domain:concept.domain,status,mastery:score,prerequisites:[...concept.prerequisites],mathDependencies:[...concept.mathDependencies]};
    });
  }
  snapshot(studentId:number): LearnerSnapshot {
    const session = this.store.getSession(studentId);
    const mastery = this.store.getMastery(studentId);
    const next = chooseNextPhysicsConcept(mastery);
    const current = session?.currentConcept ?? null;
    return { studentId, status:(session?.status ?? 'new') as LearningStatus, currentConcept:current, nextConcept:next?.id ?? null, mastery, missingRequirements:next ? missingRequirements(mastery,next.id) : [], openMisconceptions:this.store.listOpenMisconceptions(studentId).length, resume:this.store.getResume(studentId), dueReviews:this.store.getDueReviews(studentId), journey:this.journey(studentId) };
  }
  setCurrent(studentId:number, conceptId:string): void {
    getConcept(conceptId);
    const mastery = this.store.getMastery(studentId);
    const missing = missingRequirements(mastery, conceptId);
    if (missing.length) throw new Error(`Cannot start ${conceptId}; requirements not yet demonstrated: ${missing.join(', ')}`);
    this.store.saveSession(studentId, 'learning', conceptId, 0);
  }
  saveResume(studentId:number, lessonId:string, problemId:string|null, step:number): void { this.store.saveResume(studentId,lessonId,problemId,step); }
  recordAttempt(studentId:number, conceptId:string, correct:boolean, note=''): LearnerSnapshot {
    getConcept(conceptId);
    this.store.recordMastery(studentId, conceptId, correct);
    this.store.addEvidence(studentId, conceptId, 'attempt', correct ? 1 : 0, note);
    this.store.scheduleReview(studentId, conceptId, correct);
    this.store.saveSession(studentId, 'learning', conceptId, 0);
    return this.snapshot(studentId);
  }
  recordMisconception(studentId:number, conceptId:string, code:string, note:string): MisconceptionRecord { getConcept(conceptId); return this.store.addMisconception(studentId,conceptId,code,note); }
  listOpenMisconceptions(studentId:number, conceptId?:string): MisconceptionRecord[] { return this.store.listOpenMisconceptions(studentId,conceptId); }
  resolveMisconception(id:number): void { this.store.resolveMisconception(id); }
  placeByDemonstratedMastery(studentId:number, scores:Record<string,number>): LearnerSnapshot {
    for (const [conceptId,score] of Object.entries(scores)) { getConcept(conceptId); this.store.setMastery(studentId, conceptId, score); this.store.addEvidence(studentId, conceptId, 'placement', score, 'Demonstrated ability placement'); }
    this.store.saveSession(studentId, 'learning', null, 0);
    return this.snapshot(studentId);
  }
}
