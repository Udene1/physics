CREATE OR REPLACE FUNCTION vita_guard_review_consumption() RETURNS trigger AS $$
DECLARE
  current_due TIMESTAMPTZ;
BEGIN
  SELECT due_at
    INTO current_due
    FROM concept_reviews
   WHERE student_id = NEW.student_id
     AND concept_id = NEW.concept_id
   FOR UPDATE;

  IF current_due IS NULL THEN
    RAISE EXCEPTION 'No scheduled review exists for learner and concept';
  END IF;

  IF current_due > NEW.created_at THEN
    RAISE EXCEPTION 'Review is no longer due; another attempt already consumed the scheduled review';
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS review_attempt_consumption_guard ON review_attempts;
CREATE TRIGGER review_attempt_consumption_guard
BEFORE INSERT ON review_attempts
FOR EACH ROW EXECUTE FUNCTION vita_guard_review_consumption();

INSERT INTO schema_migrations(version)
VALUES ('009_review_consumption_guard')
ON CONFLICT DO NOTHING;
