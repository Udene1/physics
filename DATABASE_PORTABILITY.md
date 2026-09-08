# Database portability

Vita currently uses real SQLite through `node:sqlite` because it is simple to deploy and works well for the current learning core.

The learning engine does **not** depend on SQLite directly. Its constructor accepts the `LearningRepository` contract in `src/learning-repository.ts`. `LearningStore` is the current SQLite implementation of that contract.

The repository contract also exposes a transaction boundary. Learner-state mutations such as a problem submission, diagnostic write, placement, or mastery update are therefore atomic at the repository boundary. A PostgreSQL adapter must preserve that semantic guarantee.

## SQLite migrations

SQLite schema changes are versioned in `src/sqlite-migrations.ts`. The store creates the baseline tables and then runs additive migrations. This avoids relying on `CREATE TABLE IF NOT EXISTS` to modify an already-deployed table.

Migration rules:

- migrations are forward-only and versioned;
- migrations must be additive or explicitly data-safe;
- never silently discard learner evidence, attempts, misconceptions, resume state, or reviews;
- every schema change that matters to production gets a real integration test;
- do not use a test-only schema that differs from the runtime schema.

## Later PostgreSQL migration

A PostgreSQL migration should add a `PostgresLearningRepository` implementing the same interface. The engine, curriculum, problem model, reasoning diagnosis and learner-state semantics should remain unchanged.

The migration work then consists of:

1. Create PostgreSQL schema migrations corresponding to the repository data model.
2. Implement the repository methods with parameterized PostgreSQL queries.
3. Preserve the repository transaction boundary and rollback semantics.
4. Export the PostgreSQL adapter from the application composition root.
5. Run the same integration contract suite against PostgreSQL, using a real PostgreSQL instance rather than mocks.
6. Backfill SQLite data into PostgreSQL and verify row counts, foreign keys, mastery/evidence consistency, misconception status, resume state and review schedules.
7. Run a dual-read verification period if production scale makes a cutover risky.
8. Switch production configuration to the PostgreSQL adapter only after the verification passes.

SQLite-specific details such as `PRAGMA`, `node:sqlite`, SQLite DDL and SQLite migration mechanics stay isolated in the persistence adapter. Do not let SQL queries leak into the learning engine.

This is an adapter migration, not a rewrite of the learning system. The durable learner-state contract is the thing we migrate; the database technology is replaceable infrastructure.
