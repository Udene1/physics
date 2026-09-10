BEGIN;

CREATE TABLE IF NOT EXISTS students (
  id BIGSERIAL PRIMARY KEY,
  nickname TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mastery (
  student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  concept_id TEXT NOT NULL,
  score DOUBLE PRECISION NOT NULL CHECK (score >= 0 AND score <= 100),
  attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  correct INTEGER NOT NULL DEFAULT 0 CHECK (correct >= 0 AND correct <= attempts),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (student_id, concept_id)
);

CREATE TABLE IF NOT EXISTS learner_sessions (
  student_id BIGINT PRIMARY KEY REFERENCES students(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('new','diagnostic','learning')),
  current_concept TEXT,
  diagnostic_index INTEGER NOT NULL DEFAULT 0 CHECK (diagnostic_index >= 0),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evidence (
  id BIGSERIAL PRIMARY KEY,
  student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  concept_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  value DOUBLE PRECISION,
  note TEXT,
  lesson_id TEXT,
  problem_id TEXT,
  reasoning TEXT,
  confidence DOUBLE PRECISION CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
  hint_used BOOLEAN NOT NULL DEFAULT false,
  duration_seconds INTEGER CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS evidence_student_concept_created_idx
  ON evidence(student_id, concept_id, created_at DESC);

CREATE TABLE IF NOT EXISTS misconceptions (
  id BIGSERIAL PRIMARY KEY,
  student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  concept_id TEXT NOT NULL,
  code TEXT NOT NULL,
  severity INTEGER NOT NULL DEFAULT 1 CHECK (severity >= 1 AND severity <= 5),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','resolved')),
  occurrences INTEGER NOT NULL DEFAULT 1 CHECK (occurrences >= 1),
  last_evidence_id BIGINT REFERENCES evidence(id) ON DELETE SET NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(student_id, concept_id, code)
);

CREATE TABLE IF NOT EXISTS misconception_state (
  misconception_id BIGINT PRIMARY KEY REFERENCES misconceptions(id) ON DELETE CASCADE,
  confidence INTEGER NOT NULL DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 100),
  positive_evidence INTEGER NOT NULL DEFAULT 0 CHECK (positive_evidence >= 0),
  negative_evidence INTEGER NOT NULL DEFAULT 0 CHECK (negative_evidence >= 0),
  last_verdict TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS interventions (
  id BIGSERIAL PRIMARY KEY,
  student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  misconception_id BIGINT NOT NULL REFERENCES misconceptions(id) ON DELETE CASCADE,
  concept_id TEXT NOT NULL,
  prerequisite_concept_id TEXT NOT NULL,
  problem_id TEXT NOT NULL,
  stage TEXT NOT NULL CHECK (stage IN ('discrimination','transfer')),
  strategy TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','active','completed','blocked')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS interventions_student_status_idx
  ON interventions(student_id, status, id);

CREATE TABLE IF NOT EXISTS remediation_attempts (
  id BIGSERIAL PRIMARY KEY,
  intervention_id BIGINT NOT NULL REFERENCES interventions(id) ON DELETE CASCADE,
  evidence_id BIGINT NOT NULL REFERENCES evidence(id) ON DELETE RESTRICT,
  verdict TEXT NOT NULL,
  checkpoint_score DOUBLE PRECISION NOT NULL CHECK (checkpoint_score >= 0 AND checkpoint_score <= 1),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS concept_reviews (
  student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  concept_id TEXT NOT NULL,
  due_at TIMESTAMPTZ NOT NULL,
  interval_days INTEGER NOT NULL DEFAULT 1 CHECK (interval_days >= 1),
  streak INTEGER NOT NULL DEFAULT 0 CHECK (streak >= 0),
  last_score DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (last_score >= 0 AND last_score <= 1),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(student_id, concept_id)
);

CREATE INDEX IF NOT EXISTS concept_reviews_due_idx
  ON concept_reviews(student_id, due_at);

CREATE TABLE IF NOT EXISTS review_attempts (
  id BIGSERIAL PRIMARY KEY,
  student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  concept_id TEXT NOT NULL,
  problem_id TEXT NOT NULL,
  evidence_id BIGINT NOT NULL REFERENCES evidence(id) ON DELETE RESTRICT,
  outcome TEXT NOT NULL,
  checkpoint_score DOUBLE PRECISION NOT NULL CHECK (checkpoint_score >= 0 AND checkpoint_score <= 1),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS resume_state (
  student_id BIGINT PRIMARY KEY REFERENCES students(id) ON DELETE CASCADE,
  lesson_id TEXT,
  problem_id TEXT,
  step INTEGER NOT NULL DEFAULT 0 CHECK (step >= 0),
  state_json JSONB,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO schema_migrations(version) VALUES ('001_vita_core') ON CONFLICT DO NOTHING;

COMMIT;
