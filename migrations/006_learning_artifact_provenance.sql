CREATE TABLE IF NOT EXISTS learning_artifacts (
  id BIGSERIAL PRIMARY KEY,
  student_id BIGINT REFERENCES students(id) ON DELETE SET NULL,
  artifact_kind TEXT NOT NULL CHECK (artifact_kind IN ('lesson','explanation','hint','problem','remediation_problem','review_problem','teacher_summary')),
  content JSONB NOT NULL,
  generation_context JSONB NOT NULL DEFAULT '{}'::jsonb,
  model_provider TEXT,
  model_name TEXT,
  model_version TEXT,
  prompt_template_version TEXT,
  curriculum_version TEXT,
  validation_status TEXT NOT NULL DEFAULT 'unvalidated' CHECK (validation_status IN ('unvalidated','validated','rejected')),
  training_eligible BOOLEAN NOT NULL DEFAULT false,
  retention_class TEXT NOT NULL DEFAULT 'standard' CHECK (retention_class IN ('standard','extended','restricted')),
  expires_at TIMESTAMPTZ,
  deleted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS learning_artifacts_student_created_idx
  ON learning_artifacts(student_id, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS learning_artifacts_kind_created_idx
  ON learning_artifacts(artifact_kind, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS learning_artifacts_training_idx
  ON learning_artifacts(training_eligible, validation_status, created_at DESC);

INSERT INTO schema_migrations(version) VALUES ('006_learning_artifact_provenance') ON CONFLICT DO NOTHING;
