# Adaptive Learner Engineering Milestone

The learning system is built around a durable learner model, not a chat transcript.

## Completed foundation
- TypeScript/Node learning core established as the target runtime.
- Five-domain physics spine with targeted math dependencies and engineering application layer.
- Cross-stage placement and prerequisite-aware progression.
- Real SQLite-backed learner state; no mock learner state or mocked LLM behavior.

## Completed in this slice
- Repeated attempt evidence remains durable.
- Misconception records can be created, listed and resolved.
- Exact lesson/problem/step resume state is persisted.
- Correct/incorrect attempts schedule real spaced reviews with deterministic intervals.

## Next implementation slices
1. Build an evidence-weighted diagnostic rather than relying on one-shot scores.
2. Make remediation first-class: a misconception should produce a targeted prerequisite or alternative explanation, then require a retry before resolution.
3. Build the student-facing journey from the curriculum graph and durable state.
4. Add structured lessons/problems with real reasoning capture.
5. Connect demonstrated mastery to progressively harder engineering challenges and simulation.
6. Remove remaining Python runtime paths once their real capabilities have TypeScript replacements.

## Product rule
A learner may enter at any age, school stage, or exam stage. Placement is evidence-based. A strong learner advances; a weak prerequisite triggers intervention. The system never resets a learner merely because a new session or model starts.

See `VITA_VISION.md` for the permanent vision, guardrails and drift test.
