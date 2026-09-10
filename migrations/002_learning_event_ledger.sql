CREATE TABLE IF NOT EXISTS learning_events (
  id BIGSERIAL PRIMARY KEY,
  student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  aggregate_type TEXT NOT NULL,
  aggregate_id TEXT,
  concept_id TEXT,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS learning_events_student_created_idx
  ON learning_events(student_id, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS learning_events_student_type_idx
  ON learning_events(student_id, event_type, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS learning_events_aggregate_idx
  ON learning_events(aggregate_type, aggregate_id, created_at DESC, id DESC);
INSERT INTO schema_migrations(version) VALUES ('002_learning_event_ledger') ON CONFLICT DO NOTHING;
