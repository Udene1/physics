BEGIN;

CREATE OR REPLACE FUNCTION vita_log_intervention_event()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO learning_events (student_id,event_type,aggregate_type,aggregate_id,concept_id,payload)
    VALUES (NEW.student_id,'intervention.queued','intervention',NEW.id::text,NEW.concept_id,
            jsonb_build_object('problemId',NEW.problem_id,'stage',NEW.stage,'strategy',NEW.strategy,'status',NEW.status));
  ELSIF NEW.status IS DISTINCT FROM OLD.status THEN
    INSERT INTO learning_events (student_id,event_type,aggregate_type,aggregate_id,concept_id,payload)
    VALUES (NEW.student_id,'intervention.status_changed','intervention',NEW.id::text,NEW.concept_id,
            jsonb_build_object('problemId',NEW.problem_id,'stage',NEW.stage,'fromStatus',OLD.status,'toStatus',NEW.status));
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS intervention_learning_event ON interventions;
CREATE TRIGGER intervention_learning_event
AFTER INSERT OR UPDATE OF status ON interventions
FOR EACH ROW EXECUTE FUNCTION vita_log_intervention_event();

CREATE OR REPLACE FUNCTION vita_log_misconception_event()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO learning_events (student_id,event_type,aggregate_type,aggregate_id,concept_id,payload)
    VALUES (NEW.student_id,'misconception.created','misconception',NEW.id::text,NEW.concept_id,
            jsonb_build_object('code',NEW.code,'severity',NEW.severity,'status',NEW.status));
  ELSIF NEW.status IS DISTINCT FROM OLD.status THEN
    INSERT INTO learning_events (student_id,event_type,aggregate_type,aggregate_id,concept_id,payload)
    VALUES (NEW.student_id,'misconception.status_changed','misconception',NEW.id::text,NEW.concept_id,
            jsonb_build_object('code',NEW.code,'fromStatus',OLD.status,'toStatus',NEW.status));
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS misconception_learning_event ON misconceptions;
CREATE TRIGGER misconception_learning_event
AFTER INSERT OR UPDATE OF status ON misconceptions
FOR EACH ROW EXECUTE FUNCTION vita_log_misconception_event();

INSERT INTO schema_migrations(version) VALUES ('009_learning_state_events')
ON CONFLICT (version) DO NOTHING;

COMMIT;
