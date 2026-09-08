# Adaptive Learner Engineering Milestone

The learning system is built around a durable learner model, not a chat transcript.

## Completed foundation
- TypeScript/Node learning core established as the target runtime.
- Five-domain physics spine with targeted math dependencies and engineering application layer.
- Cross-stage placement and prerequisite-aware progression.
- Real SQLite-backed learner state; no mock learner state or mocked LLM behavior.

## Completed adaptive core
- Repeated evidence remains durable and queryable.
- Evidence-weighted diagnostic aggregates the learner's history instead of treating every diagnostic as a reset.
- Misconceptions are durable and cannot be manually resolved; successful targeted retry is the resolution gate.
- Reasoning produces structured signals, coverage and misconception codes.
- Exact lesson/problem/step resume is persisted and validated against real content.
- Correct/incorrect attempts schedule deterministic spaced reviews.
- Deterministic next-action routing prioritizes remediation, review, learning and eventual building.
- Structured lessons follow Observe → Model → Math → Predict → Test → Explain.
- Physics problems now cover mechanics, energy, momentum, waves, circuits and Modern Physics.
- Engineering challenges unlock from demonstrated physics mastery and include safety boundaries.
- Modern Physics specialization choice is durable and gated by the selected branch's prerequisites.
- SQLite schema is versioned through migration 4 with production-oriented indexes.
- PostgreSQL baseline schema mirrors the durable learner-state contract.

## Next implementation slices
1. Build the actual learner-facing application/API around these engine contracts.
2. Replace keyword-only reasoning detection with richer structured claims, equations, units, vectors and conceptual relations while retaining deterministic tests.
3. Add real transfer assessments and adaptive diagnostic item selection across the five physics domains.
4. Persist engineering project attempts, measurements, predictions and experiment results.
5. Add a real simulation boundary for prediction → experiment → comparison.
6. Implement the PostgreSQL repository and run the same integration contract against a real PostgreSQL instance before production cutover.
7. Remove remaining Python runtime paths once every real capability has a TypeScript replacement.

## Product rule
A learner may enter at any age, school stage, or exam stage. Placement is evidence-based. A strong learner advances; a weak prerequisite triggers intervention. The system never resets a learner merely because a new session or model starts.

See `VITA_VISION.md` for the permanent vision, guardrails and drift test.
