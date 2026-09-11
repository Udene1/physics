CREATE TABLE IF NOT EXISTS classrooms (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL CHECK (length(trim(name)) >= 2),
  code TEXT NOT NULL UNIQUE CHECK (length(trim(code)) >= 4),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS classroom_students (
  classroom_id BIGINT NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
  student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (classroom_id, student_id)
);

CREATE INDEX IF NOT EXISTS classroom_students_student_idx
  ON classroom_students(student_id, classroom_id);

INSERT INTO schema_migrations(version)
VALUES ('013_classroom_learning_intelligence')
ON CONFLICT (version) DO NOTHING;
