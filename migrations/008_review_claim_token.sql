ALTER TABLE concept_reviews
  ADD COLUMN IF NOT EXISTS revision BIGINT NOT NULL DEFAULT 0 CHECK (revision >= 0);

INSERT INTO schema_migrations(version)
VALUES ('008_review_claim_token')
ON CONFLICT DO NOTHING;
