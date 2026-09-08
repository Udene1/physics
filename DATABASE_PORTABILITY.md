# Database portability

Vita currently uses real SQLite through `node:sqlite` because it is simple to deploy and works well for the current single-process learning core.

The learning engine does **not** depend on SQLite directly. Its constructor accepts the `LearningRepository` contract in `src/learning-repository.ts`. `LearningStore` is the current SQLite implementation of that contract.

## Later PostgreSQL migration

A PostgreSQL migration should add a `PostgresLearningRepository` implementing the same interface. The engine, curriculum, problem model, reasoning diagnosis and learner-state semantics should remain unchanged.

The migration work then consists of:

1. Create PostgreSQL schema/migrations for the repository tables.
2. Implement the repository methods using parameterized PostgreSQL queries.
3. Export the PostgreSQL adapter from the application composition root.
4. Run the same integration test suite against PostgreSQL.
5. Backfill SQLite data into PostgreSQL and verify row counts/state invariants.
6. Switch production configuration to the PostgreSQL adapter.

SQLite-specific details such as `PRAGMA`, `node:sqlite`, and SQLite DDL stay isolated in the persistence adapter. Do not let SQL queries leak into the learning engine.

This is an adapter migration, not a rewrite of the learning system.
