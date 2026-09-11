ALTER TABLE remediation_attempts
  DROP CONSTRAINT IF EXISTS remediation_attempts_evidence_id_fkey;
ALTER TABLE remediation_attempts
  ADD CONSTRAINT remediation_attempts_evidence_id_fkey
  FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE;

ALTER TABLE review_attempts
  DROP CONSTRAINT IF EXISTS review_attempts_evidence_id_fkey;
ALTER TABLE review_attempts
  ADD CONSTRAINT review_attempts_evidence_id_fkey
  FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE;

INSERT INTO schema_migrations(version) VALUES ('016_evidence_cleanup_integrity') ON CONFLICT (version) DO NOTHING;
