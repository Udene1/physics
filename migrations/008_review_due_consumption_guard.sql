BEGIN;

CREATE OR REPLACE FUNCTION vita_require_due_review()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  due_at_value timestamptz;
BEGIN
  SELECT due_at
    INTO due_at_value
    FROM concept_reviews
   WHERE student_id = NEW.student_id
     AND concept_id = NEW.concept_id
   FOR UPDATE;

  IF due_at_value IS NULL THEN
    RAISE EXCEPTION 'review is not scheduled for learner and concept';
  END IF;

  IF due_at_value > now() THEN
    RAISE EXCEPTION 'review is not due for learner and concept';
  END IF;

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS review_attempts_require_due_review ON review_attempts;
CREATE TRIGGER review_attempts_require_due_review
BEFORE INSERT ON review_attempts
FOR EACH ROW
EXECUTE FUNCTION vita_require_due_review();

INSERT INTO schema_migrations(version) VALUES ('008_review_due_consumption_guard')
ON CONFLICT (version) DO NOTHING;

COMMIT;
