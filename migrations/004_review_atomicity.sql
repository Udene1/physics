ALTER TABLE review_attempts
  ADD COLUMN IF NOT EXISTS outcome TEXT NOT NULL DEFAULT 'insufficient_evidence';

CREATE INDEX IF NOT EXISTS review_attempts_student_created_idx
  ON review_attempts(student_id, created_at DESC, id DESC);

INSERT INTO schema_migrations(version)
VALUES ('004_review_atomicity')
ON CONFLICT DO NOTHING;
