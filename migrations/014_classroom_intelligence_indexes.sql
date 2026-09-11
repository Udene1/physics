CREATE INDEX IF NOT EXISTS mastery_student_concept_idx
  ON mastery(student_id, concept_id);

CREATE INDEX IF NOT EXISTS misconceptions_student_status_idx
  ON misconceptions(student_id, status, concept_id);

CREATE INDEX IF NOT EXISTS remediation_attempts_intervention_verdict_idx
  ON remediation_attempts(intervention_id, verdict);

CREATE INDEX IF NOT EXISTS concept_reviews_due_lookup_idx
  ON concept_reviews(student_id, due_at, concept_id);

INSERT INTO schema_migrations(version)
VALUES ('014_classroom_intelligence_indexes')
ON CONFLICT (version) DO NOTHING;
