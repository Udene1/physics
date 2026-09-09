import { DatabaseSync } from 'node:sqlite';
import { mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

export interface MasteryRecord { studentId:number; conceptId:string; score:number; attempts:number; correct:number; updatedAt:string; }
export interface EvidenceInput { kind:string; value?:number|null; note?:string; lessonId?:string|null; problemId?:string|null; reasoning?:string|null; confidence?:number|null; hintUsed?:boolean; durationSeconds?:number|null; }
export interface MisconceptionRecord { id:number; studentId:number; conceptId:string; code:string; severity:number; status:'active'|'resolved'; occurrences:number; lastEvidenceId:number|null; updatedAt:string; }
export interface ResumeState { lessonId:string|null; problemId:string|null; step:number; stateJson:string|null; updatedAt:string; }

export class LearningStore {
  readonly db: DatabaseSync;
  constructor(path = process.env.VITA_DB_PATH ?? './data/vita.sqlite') {
    if (path !== ':memory:') mkdirSync(dirname(path), { recursive: true });
    this.db = new DatabaseSync(path);
    this.db.exec('PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL; PRAGMA synchronous = NORMAL;');
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, nickname TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS mastery (student_id INTEGER NOT NULL, concept_id TEXT NOT NULL, score REAL NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0, correct INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL, PRIMARY KEY(student_id, concept_id), FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE);
      CREATE TABLE IF NOT EXISTS learner_sessions (student_id INTEGER PRIMARY KEY, status TEXT NOT NULL, current_concept TEXT, diagnostic_index INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL, FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE);
      CREATE TABLE IF NOT EXISTS evidence (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, concept_id TEXT NOT NULL, kind TEXT NOT NULL, value REAL, note TEXT, lesson_id TEXT, problem_id TEXT, reasoning TEXT, confidence REAL, hint_used INTEGER NOT NULL DEFAULT 0, duration_seconds INTEGER, created_at TEXT NOT NULL, FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE);
      CREATE TABLE IF NOT EXISTS misconceptions (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, concept_id TEXT NOT NULL, code TEXT NOT NULL, severity INTEGER NOT NULL DEFAULT 1, status TEXT NOT NULL DEFAULT 'active', occurrences INTEGER NOT NULL DEFAULT 1, last_evidence_id INTEGER, updated_at TEXT NOT NULL, UNIQUE(student_id, concept_id, code), FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE, FOREIGN KEY(last_evidence_id) REFERENCES evidence(id) ON DELETE SET NULL);
      CREATE TABLE IF NOT EXISTS resume_state (student_id INTEGER PRIMARY KEY, lesson_id TEXT, problem_id TEXT, step INTEGER NOT NULL DEFAULT 0, state_json TEXT, updated_at TEXT NOT NULL, FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE);
    `);
  }
  close(): void { this.db.close(); }
  ensureStudent(nickname: string): number {
    const existing = this.db.prepare('SELECT id FROM students WHERE nickname = ?').get(nickname) as {id:number}|undefined;
    if (existing) return existing.id;
    const result = this.db.prepare('INSERT INTO students(nickname, created_at) VALUES (?, ?)').run(nickname, new Date().toISOString());
    return Number(result.lastInsertRowid);
  }
  getMastery(studentId:number): Record<string,number> {
    const rows = this.db.prepare('SELECT concept_id, score FROM mastery WHERE student_id = ?').all(studentId) as Array<{concept_id:string;score:number}>;
    return Object.fromEntries(rows.map(r => [r.concept_id, r.score]));
  }
  recordMastery(studentId:number, conceptId:string, correct:boolean): MasteryRecord {
    const now = new Date().toISOString();
    const current = this.db.prepare('SELECT score, attempts, correct FROM mastery WHERE student_id = ? AND concept_id = ?').get(studentId, conceptId) as {score:number;attempts:number;correct:number}|undefined;
    const attempts = (current?.attempts ?? 0) + 1;
    const correctCount = (current?.correct ?? 0) + (correct ? 1 : 0);
    const score = Math.round((correctCount / attempts) * 1000) / 10;
    this.db.prepare(`INSERT INTO mastery(student_id, concept_id, score, attempts, correct, updated_at) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(student_id, concept_id) DO UPDATE SET score=excluded.score, attempts=excluded.attempts, correct=excluded.correct, updated_at=excluded.updated_at`).run(studentId, conceptId, score, attempts, correctCount, now);
    return {studentId, conceptId, score, attempts, correct:correctCount, updatedAt:now};
  }
  setMastery(studentId:number, conceptId:string, score:number): void {
    if (!Number.isFinite(score) || score < 0 || score > 100) throw new Error('Mastery score must be between 0 and 100');
    const now = new Date().toISOString();
    this.db.prepare(`INSERT INTO mastery(student_id, concept_id, score, updated_at) VALUES (?, ?, ?, ?) ON CONFLICT(student_id, concept_id) DO UPDATE SET score=excluded.score, updated_at=excluded.updated_at`).run(studentId, conceptId, score, now);
  }
  saveSession(studentId:number, status:string, currentConcept:string|null, diagnosticIndex:number): void {
    this.db.prepare(`INSERT INTO learner_sessions(student_id,status,current_concept,diagnostic_index,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(student_id) DO UPDATE SET status=excluded.status,current_concept=excluded.current_concept,diagnostic_index=excluded.diagnostic_index,updated_at=excluded.updated_at`).run(studentId,status,currentConcept,diagnosticIndex,new Date().toISOString());
  }
  getSession(studentId:number): {status:string;currentConcept:string|null;diagnosticIndex:number}|undefined {
    const row = this.db.prepare('SELECT status, current_concept, diagnostic_index FROM learner_sessions WHERE student_id = ?').get(studentId) as {status:string;current_concept:string|null;diagnostic_index:number}|undefined;
    return row ? {status:row.status,currentConcept:row.current_concept,diagnosticIndex:row.diagnostic_index} : undefined;
  }
  addEvidence(studentId:number, conceptId:string, input:string|EvidenceInput, value:number|null = null, note=''): number {
    const e: EvidenceInput = typeof input === 'string' ? {kind:input, value, note} : input;
    const result = this.db.prepare('INSERT INTO evidence(student_id,concept_id,kind,value,note,lesson_id,problem_id,reasoning,confidence,hint_used,duration_seconds,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)').run(studentId,conceptId,e.kind,e.value ?? null,e.note ?? null,e.lessonId ?? null,e.problemId ?? null,e.reasoning ?? null,e.confidence ?? null,e.hintUsed ? 1 : 0,e.durationSeconds ?? null,new Date().toISOString());
    return Number(result.lastInsertRowid);
  }
  upsertMisconception(studentId:number, conceptId:string, code:string, severity:number, evidenceId:number|null): MisconceptionRecord {
    if (!Number.isInteger(severity) || severity < 1 || severity > 5) throw new Error('Misconception severity must be between 1 and 5');
    const now = new Date().toISOString();
    this.db.prepare(`INSERT INTO misconceptions(student_id,concept_id,code,severity,status,occurrences,last_evidence_id,updated_at) VALUES(?,?,?,?, 'active',1,?,?) ON CONFLICT(student_id,concept_id,code) DO UPDATE SET severity=excluded.severity,status='active',occurrences=misconceptions.occurrences+1,last_evidence_id=excluded.last_evidence_id,updated_at=excluded.updated_at`).run(studentId,conceptId,code,severity,evidenceId,now);
    return this.db.prepare('SELECT id,student_id,concept_id,code,severity,status,occurrences,last_evidence_id,updated_at FROM misconceptions WHERE student_id=? AND concept_id=? AND code=?').get(studentId,conceptId,code) as MisconceptionRecord;
  }
  listMisconceptions(studentId:number, conceptId?:string): MisconceptionRecord[] {
    const rows = conceptId
      ? this.db.prepare('SELECT id,student_id,concept_id,code,severity,status,occurrences,last_evidence_id,updated_at FROM misconceptions WHERE student_id=? AND concept_id=? ORDER BY severity DESC, updated_at DESC').all(studentId,conceptId)
      : this.db.prepare('SELECT id,student_id,concept_id,code,severity,status,occurrences,last_evidence_id,updated_at FROM misconceptions WHERE student_id=? ORDER BY severity DESC, updated_at DESC').all(studentId);
    return rows as MisconceptionRecord[];
  }
  resolveMisconception(studentId:number, misconceptionId:number): void {
    this.db.prepare("UPDATE misconceptions SET status='resolved', updated_at=? WHERE id=? AND student_id=?").run(new Date().toISOString(),misconceptionId,studentId);
  }
  saveResume(studentId:number, lessonId:string|null, problemId:string|null, step:number, state:unknown = null): void {
    if (!Number.isInteger(step) || step < 0) throw new Error('Resume step must be a non-negative integer');
    const stateJson = state === null ? null : JSON.stringify(state);
    this.db.prepare(`INSERT INTO resume_state(student_id,lesson_id,problem_id,step,state_json,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(student_id) DO UPDATE SET lesson_id=excluded.lesson_id,problem_id=excluded.problem_id,step=excluded.step,state_json=excluded.state_json,updated_at=excluded.updated_at`).run(studentId,lessonId,problemId,step,stateJson,new Date().toISOString());
  }
  getResume(studentId:number): ResumeState|undefined {
    const row = this.db.prepare('SELECT lesson_id,problem_id,step,state_json,updated_at FROM resume_state WHERE student_id=?').get(studentId) as {lesson_id:string|null;problem_id:string|null;step:number;state_json:string|null;updated_at:string}|undefined;
    return row ? {lessonId:row.lesson_id,problemId:row.problem_id,step:row.step,stateJson:row.state_json,updatedAt:row.updated_at} : undefined;
  }
}
