CREATE OR REPLACE FUNCTION vita_log_misconception_state_change() RETURNS trigger AS $$
BEGIN
  IF NEW.status IS DISTINCT FROM OLD.status
     OR NEW.severity IS DISTINCT FROM OLD.severity
     OR NEW.occurrences IS DISTINCT FROM OLD.occurrences THEN
    INSERT INTO learning_events(student_id,event_type,aggregate_type,aggregate_id,concept_id,payload)
    VALUES (
      NEW.student_id,
      'misconception.state_changed',
      'misconception',
      NEW.id::text,
      NEW.concept_id,
      jsonb_build_object(
        'previousStatus', OLD.status,
        'status', NEW.status,
        'severity', NEW.severity,
        'occurrences', NEW.occurrences,
        'lastEvidenceId', NEW.last_evidence_id
      )
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS misconception_state_learning_event ON misconceptions;
CREATE TRIGGER misconception_state_learning_event
AFTER UPDATE ON misconceptions
FOR EACH ROW EXECUTE FUNCTION vita_log_misconception_state_change();

CREATE OR REPLACE FUNCTION vita_log_intervention_state_change() RETURNS trigger AS $$
BEGIN
  IF NEW.status IS DISTINCT FROM OLD.status THEN
    INSERT INTO learning_events(student_id,event_type,aggregate_type,aggregate_id,concept_id,payload)
    VALUES (
      NEW.student_id,
      'intervention.state_changed',
      'intervention',
      NEW.id::text,
      NEW.concept_id,
      jsonb_build_object(
        'previousStatus', OLD.status,
        'status', NEW.status,
        'stage', NEW.stage,
        'problemId', NEW.problem_id,
        'misconceptionId', NEW.misconception_id
      )
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS intervention_state_learning_event ON interventions;
CREATE TRIGGER intervention_state_learning_event
AFTER UPDATE ON interventions
FOR EACH ROW EXECUTE FUNCTION vita_log_intervention_state_change();

INSERT INTO schema_migrations(version)
VALUES ('010_learning_state_events')
ON CONFLICT DO NOTHING;
