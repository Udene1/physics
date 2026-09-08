-- Vita PostgreSQL baseline. Keep column names and semantics aligned with LearningRepository.
CREATE TABLE students (id BIGSERIAL PRIMARY KEY, nickname TEXT NOT NULL UNIQUE, created_at TIMESTAMPTZ NOT NULL);
CREATE TABLE mastery (student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE, concept_id TEXT NOT NULL, score DOUBLE PRECISION NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0, correct INTEGER NOT NULL DEFAULT 0, updated_at TIMESTAMPTZ NOT NULL, PRIMARY KEY(student_id, concept_id));
CREATE TABLE learner_sessions (student_id BIGINT PRIMARY KEY REFERENCES students(id) ON DELETE CASCADE, status TEXT NOT NULL, current_concept TEXT, diagnostic_index INTEGER NOT NULL DEFAULT 0, updated_at TIMESTAMPTZ NOT NULL);
CREATE TABLE evidence (id BIGSERIAL PRIMARY KEY, student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE, concept_id TEXT NOT NULL, kind TEXT NOT NULL, value DOUBLE PRECISION, note TEXT NOT NULL DEFAULT '', created_at TIMESTAMPTZ NOT NULL);
CREATE TABLE misconceptions (id BIGSERIAL PRIMARY KEY, student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE, concept_id TEXT NOT NULL, code TEXT NOT NULL, note TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open', created_at TIMESTAMPTZ NOT NULL, resolved_at TIMESTAMPTZ);
CREATE TABLE resume_state (student_id BIGINT PRIMARY KEY REFERENCES students(id) ON DELETE CASCADE, lesson_id TEXT NOT NULL, problem_id TEXT, step INTEGER NOT NULL DEFAULT 0, updated_at TIMESTAMPTZ NOT NULL);
CREATE TABLE reviews (student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE, concept_id TEXT NOT NULL, due_at TIMESTAMPTZ NOT NULL, interval_days INTEGER NOT NULL DEFAULT 1, repetitions INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(student_id, concept_id));
CREATE TABLE problem_attempts (id BIGSERIAL PRIMARY KEY, student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE, problem_id TEXT NOT NULL, concept_id TEXT NOT NULL, answer TEXT NOT NULL, correct BOOLEAN NOT NULL, reasoning TEXT NOT NULL, confidence DOUBLE PRECISION, reasoning_signals JSONB NOT NULL DEFAULT '[]'::jsonb, misconception_codes JSONB NOT NULL DEFAULT '[]'::jsonb, created_at TIMESTAMPTZ NOT NULL);
CREATE TABLE modern_specializations (student_id BIGINT PRIMARY KEY REFERENCES students(id) ON DELETE CASCADE, specialization TEXT NOT NULL CHECK (specialization IN ('relativity','quantum','atomic_nuclear')), updated_at TIMESTAMPTZ NOT NULL);
CREATE INDEX idx_evidence_student_concept_created ON evidence(student_id, concept_id, created_at);
CREATE INDEX idx_attempts_student_concept_created ON problem_attempts(student_id, concept_id, created_at);
CREATE INDEX idx_misconceptions_open ON misconceptions(student_id, concept_id, status, id);
CREATE INDEX idx_reviews_due ON reviews(student_id, due_at);
