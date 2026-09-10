CREATE OR REPLACE FUNCTION vita_prevent_learning_event_mutation() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'learning_events is append-only; event mutation is not permitted';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS learning_events_immutable ON learning_events;
CREATE TRIGGER learning_events_immutable
BEFORE UPDATE OR DELETE ON learning_events
FOR EACH ROW EXECUTE FUNCTION vita_prevent_learning_event_mutation();

INSERT INTO schema_migrations(version)
VALUES ('005_immutable_learning_events')
ON CONFLICT DO NOTHING;
