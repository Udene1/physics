# Adaptive Learner Engineering Milestone

The learning system is built around a durable learner model, not a chat transcript.

## Current foundation
- Cross-stage learner discovery from foundational mathematics through introductory physics.
- Persistent diagnostic position and learner state.
- Explicit math-to-physics prerequisite graph.
- Deterministic readiness checks and learning frontier selection.
- Real SQLite-backed state; no mock learner state or mocked LLM behavior.

## Next implementation slices
1. Replace broad diagnostic-only skill scores with repeated evidence from real lessons and problems.
2. Add misconception records and targeted remediation attempts.
3. Add exact lesson/problem resume state.
4. Add spaced review scheduling.
5. Build a student-facing journey map from the same graph/state.
6. Connect demonstrated mastery to progressively harder engineering challenges.

## Product rule
A learner may enter at any age, school stage, or exam stage. Placement is evidence-based. A strong learner advances; a weak prerequisite triggers intervention. The system never resets a learner merely because a new session or model starts.
