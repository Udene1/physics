CREATE TABLE IF NOT EXISTS learning_artifact_usage (
  id BIGSERIAL PRIMARY KEY,
  artifact_id BIGINT NOT NULL REFERENCES learning_artifacts(id) ON DELETE CASCADE,
  student_id BIGINT REFERENCES students(id) ON DELETE SET NULL,
  evidence_id BIGINT REFERENCES evidence(id) ON DELETE SET NULL,
  usage_kind TEXT NOT NULL CHECK (usage_kind IN ('presented','attempted','validated','teacher_reviewed')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS learning_artifact_usage_artifact_created_idx
  ON learning_artifact_usage(artifact_id, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS learning_artifact_usage_student_created_idx
  ON learning_artifact_usage(student_id, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS learning_artifact_usage_evidence_idx
  ON learning_artifact_usage(evidence_id);

INSERT INTO schema_migrations(version) VALUES ('007_learning_artifact_usage') ON CONFLICT DO NOTHING;
