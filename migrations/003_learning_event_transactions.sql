CREATE OR REPLACE FUNCTION vita_log_remediation_event() RETURNS trigger AS $$
BEGIN
  INSERT INTO learning_events (
    student_id,
    event_type,
    aggregate_type,
    aggregate_id,
    concept_id,
    payload
  )
  SELECT
    i.student_id,
    'remediation.attempted',
    'remediation_attempt',
    NEW.id::text,
    i.concept_id,
    jsonb_build_object(
      'interventionId', NEW.intervention_id,
      'evidenceId', NEW.evidence_id,
      'verdict', NEW.verdict,
      'checkpointScore', NEW.checkpoint_score,
      'stage', i.stage
    )
  FROM interventions i
  WHERE i.id = NEW.intervention_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS remediation_attempt_learning_event ON remediation_attempts;
CREATE TRIGGER remediation_attempt_learning_event
AFTER INSERT ON remediation_attempts
FOR EACH ROW EXECUTE FUNCTION vita_log_remediation_event();

CREATE OR REPLACE FUNCTION vita_log_review_event() RETURNS trigger AS $$
BEGIN
  INSERT INTO learning_events (
    student_id,
    event_type,
    aggregate_type,
    aggregate_id,
    concept_id,
    payload
  ) VALUES (
    NEW.student_id,
    'review.attempted',
    'review_attempt',
    NEW.id::text,
    NEW.concept_id,
    jsonb_build_object(
      'problemId', NEW.problem_id,
      'evidenceId', NEW.evidence_id,
      'outcome', NEW.outcome,
      'checkpointScore', NEW.checkpoint_score
    )
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS review_attempt_learning_event ON review_attempts;
CREATE TRIGGER review_attempt_learning_event
AFTER INSERT ON review_attempts
FOR EACH ROW EXECUTE FUNCTION vita_log_review_event();

CREATE OR REPLACE FUNCTION vita_log_evidence_event() RETURNS trigger AS $$
BEGIN
  INSERT INTO learning_events (
    student_id,
    event_type,
    aggregate_type,
    aggregate_id,
    concept_id,
    payload
  ) VALUES (
    NEW.student_id,
    'evidence.recorded',
    'evidence',
    NEW.id::text,
    NEW.concept_id,
    jsonb_build_object(
      'kind', NEW.kind,
      'problemId', NEW.problem_id,
      'lessonId', NEW.lesson_id,
      'value', NEW.value,
      'confidence', NEW.confidence,
      'hintUsed', NEW.hint_used
    )
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS evidence_learning_event ON evidence;
CREATE TRIGGER evidence_learning_event
AFTER INSERT ON evidence
FOR EACH ROW EXECUTE FUNCTION vita_log_evidence_event();

INSERT INTO schema_migrations(version)
VALUES ('003_learning_event_transactions')
ON CONFLICT DO NOTHING;
