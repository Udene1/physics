import type { DatabaseSync } from 'node:sqlite';

export const SQLITE_SCHEMA_VERSION = 3;

function columns(db: DatabaseSync, table: string): Set<string> {
  const rows = db.prepare(`PRAGMA table_info(${table})`).all() as Array<{ name: string }>;
  return new Set(rows.map(row => row.name));
}

export function migrateSqlite(db: DatabaseSync): void {
  db.exec('CREATE TABLE IF NOT EXISTS schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)');
  const current = Number((db.prepare("SELECT value FROM schema_meta WHERE key='schema_version'").get() as { value: string } | undefined)?.value ?? 0);
  if (current > SQLITE_SCHEMA_VERSION) throw new Error(`Unsupported SQLite schema version: ${current}`);
  if (current < 1) db.prepare("INSERT INTO schema_meta(key,value) VALUES('schema_version','1') ON CONFLICT(key) DO UPDATE SET value='1'").run();
  if (current < 2) {
    const attemptColumns = columns(db, 'problem_attempts');
    if (attemptColumns.size > 0) {
      if (!attemptColumns.has('reasoning_signals')) db.exec("ALTER TABLE problem_attempts ADD COLUMN reasoning_signals TEXT NOT NULL DEFAULT '[]'");
      if (!attemptColumns.has('misconception_codes')) db.exec("ALTER TABLE problem_attempts ADD COLUMN misconception_codes TEXT NOT NULL DEFAULT '[]'");
    }
    db.prepare("INSERT INTO schema_meta(key,value) VALUES('schema_version','2') ON CONFLICT(key) DO UPDATE SET value='2'").run();
  }
  if (current < 3) {
    db.exec('CREATE INDEX IF NOT EXISTS idx_evidence_student_concept_created ON evidence(student_id, concept_id, created_at)');
    db.exec('CREATE INDEX IF NOT EXISTS idx_attempts_student_concept_created ON problem_attempts(student_id, concept_id, created_at)');
    db.exec('CREATE INDEX IF NOT EXISTS idx_misconceptions_open ON misconceptions(student_id, concept_id, status, id)');
    db.exec('CREATE INDEX IF NOT EXISTS idx_reviews_due ON reviews(student_id, due_at)');
    db.prepare("INSERT INTO schema_meta(key,value) VALUES('schema_version','3') ON CONFLICT(key) DO UPDATE SET value='3'").run();
  }
}
