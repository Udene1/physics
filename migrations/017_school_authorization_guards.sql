CREATE OR REPLACE FUNCTION vita_enforce_staff_school_change()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.school_id = OLD.school_id THEN
    RETURN NEW;
  END IF;
  IF EXISTS (SELECT 1 FROM classroom_staff cs WHERE cs.staff_id = NEW.id) THEN
    RAISE EXCEPTION 'staff with classroom assignments cannot change schools';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS vita_staff_school_change_guard ON school_staff;
CREATE TRIGGER vita_staff_school_change_guard
BEFORE UPDATE OF school_id ON school_staff
FOR EACH ROW EXECUTE FUNCTION vita_enforce_staff_school_change();

CREATE OR REPLACE FUNCTION vita_enforce_classroom_staff_role()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  staff_role TEXT;
BEGIN
  SELECT role INTO staff_role FROM school_staff WHERE id = NEW.staff_id;
  IF staff_role IS NULL THEN
    RAISE EXCEPTION 'assigned staff member does not exist';
  END IF;
  IF staff_role = 'admin' THEN
    RAISE EXCEPTION 'administrators cannot be classroom assignees';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS vita_classroom_staff_role_guard ON classroom_staff;
CREATE TRIGGER vita_classroom_staff_role_guard
BEFORE INSERT OR UPDATE OF staff_id ON classroom_staff
FOR EACH ROW EXECUTE FUNCTION vita_enforce_classroom_staff_role();

INSERT INTO schema_migrations(version) VALUES ('017_school_authorization_guards') ON CONFLICT (version) DO NOTHING;
