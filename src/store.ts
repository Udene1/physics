import { DatabaseSync } from 'node:sqlite';
import { mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

export interface MasteryRecord { studentId:number; conceptId:string; score:number; attempts:number; correct:number; updatedAt:string; }

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
      CREATE TABLE IF NOT EXISTS evidence (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, concept_id TEXT NOT NULL, kind TEXT NOT NULL, value REAL, note TEXT, created_at TEXT NOT NULL, FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE);
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
  addEvidence(studentId:number, conceptId:string, kind:string, value:number|null, note:string): void {
    this.db.prepare('INSERT INTO evidence(student_id,concept_id,kind,value,note,created_at) VALUES(?,?,?,?,?,?)').run(studentId,conceptId,kind,value,note,new Date().toISOString());
  }
}
