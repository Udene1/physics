CREATE TABLE IF NOT EXISTS schools (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL CHECK (length(trim(name)) >= 2),
  code TEXT NOT NULL UNIQUE CHECK (length(trim(code)) >= 2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS school_staff (
  id BIGSERIAL PRIMARY KEY,
  school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
  display_name TEXT NOT NULL CHECK (length(trim(display_name)) >= 2),
  role TEXT NOT NULL CHECK (role IN ('teacher','dean','admin')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (school_id, display_name)
);

CREATE INDEX IF NOT EXISTS school_staff_school_role_idx ON school_staff(school_id, role);

ALTER TABLE classrooms ADD COLUMN IF NOT EXISTS school_id BIGINT REFERENCES schools(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS classrooms_school_idx ON classrooms(school_id);

CREATE TABLE IF NOT EXISTS classroom_staff (
  classroom_id BIGINT NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
  staff_id BIGINT NOT NULL REFERENCES school_staff(id) ON DELETE CASCADE,
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (classroom_id, staff_id)
);

CREATE INDEX IF NOT EXISTS classroom_staff_staff_idx ON classroom_staff(staff_id, classroom_id);

CREATE OR REPLACE FUNCTION vita_enforce_classroom_school()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.school_id IS NULL THEN
    RETURN NEW;
  END IF;
  IF EXISTS (SELECT 1 FROM classroom_staff cs JOIN school_staff ss ON ss.id = cs.staff_id WHERE cs.classroom_id = NEW.id AND ss.school_id <> NEW.school_id) THEN
    RAISE EXCEPTION 'classroom staff must belong to the classroom school';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS vita_classroom_school_guard ON classrooms;
CREATE TRIGGER vita_classroom_school_guard
AFTER INSERT OR UPDATE OF school_id ON classrooms
FOR EACH ROW EXECUTE FUNCTION vita_enforce_classroom_school();

CREATE OR REPLACE FUNCTION vita_enforce_classroom_staff_school()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  classroom_school BIGINT;
  staff_school BIGINT;
BEGIN
  SELECT school_id INTO classroom_school FROM classrooms WHERE id = NEW.classroom_id;
  SELECT school_id INTO staff_school FROM school_staff WHERE id = NEW.staff_id;
  IF classroom_school IS NULL OR staff_school IS NULL THEN
    RAISE EXCEPTION 'classroom and staff must belong to a school before assignment';
  END IF;
  IF classroom_school <> staff_school THEN
    RAISE EXCEPTION 'staff cannot be assigned across schools';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS vita_classroom_staff_school_guard ON classroom_staff;
CREATE TRIGGER vita_classroom_staff_school_guard
BEFORE INSERT OR UPDATE ON classroom_staff
FOR EACH ROW EXECUTE FUNCTION vita_enforce_classroom_staff_school();

INSERT INTO schema_migrations(version) VALUES ('015_school_staff_authorization') ON CONFLICT (version) DO NOTHING;
