# Vita — Vision and Build Contract

Vita is not a generic tutoring chatbot. It is a durable learning companion whose job is to turn a learner into a capable physicist, problem solver and eventually an engineer/builder.

## North star

**Understand reality → model it → use mathematics when needed → predict → test → explain → build.**

The system should adapt to the learner's demonstrated ability rather than age, school label or conversation history.

## Non-negotiable product truths

1. **Physics is the organizing spine.** The five domains are Mechanics, Thermal Physics, Waves & Optics, Electricity & Magnetism, and Modern Physics.
2. **Mathematics is a dependency layer, not a parallel destination.** Teach or repair only the mathematics that is actually blocking the physical idea.
3. **Engineering is an application layer.** Demonstrated physical understanding should eventually unlock design, simulation, measurement and real builds.
4. **Any learner can enter anywhere.** A child can start years before formal physics; an existing physics learner or WAEC candidate can enter at their current demonstrated level.
5. **Placement is evidence-based.** Never force a strong learner through material they have already demonstrated. Never advance a learner past a prerequisite they have not demonstrated.
6. **The conversation is disposable; the learner model is not.** Mastery, evidence, misconceptions, resume state and review schedule must survive sessions, devices and model changes.
7. **No fake capability.** No mocks standing in for production behavior. Tests should exercise real persistence and real integration boundaries whenever possible.
8. **Problem solving beats exam optimization.** WAEC support is a valid entry/use case, but it must not become the identity of the platform.
9. **Modern Physics branches.** At the branch point, a learner may specialize in Relativity, Quantum, or Atomic/Nuclear physics rather than being forced through all three.
10. **Build only what we can make real.** Prefer a smaller working vertical slice over an impressive fake abstraction.

## Learner loop

**Observe → attempt → explain reasoning → diagnose misconception → repair the blocking dependency → retry → update evidence/mastery → schedule review → advance.**

A wrong answer is evidence, not simply a score. Repeated evidence matters more than one diagnostic snapshot.

## Architecture direction

- TypeScript/Node is the target runtime; Python is transitional legacy, not the target architecture.
- SQLite is the current real persistence layer and must remain student-scoped.
- The curriculum graph is the source of truth for prerequisites and progression.
- The learner state sits above the graph: mastery, evidence, misconceptions, exact resume state and review scheduling.
- Future UI, AI coaching, simulations and hardware features must consume the same durable learner state rather than inventing separate progress systems.

## Build roadmap

### Phase 1 — Foundation
- TypeScript runtime and CI
- real SQLite learner state
- physics-first curriculum graph
- deterministic prerequisite-aware routing

### Phase 2 — Adaptive learning core (current)
- repeated evidence from attempts and lessons
- misconception records and remediation loop
- exact lesson/problem resume
- spaced review
- student journey derived from the same graph/state

### Phase 3 — Real learning experience
- diagnostic that samples concepts intelligently
- structured physics lessons and real problems
- reasoning capture and misconception classification
- targeted math interventions
- mastery confidence/evidence model
- student-facing journey, missions and meaningful milestones

### Phase 4 — Physics → engineering
- progressively harder engineering challenges tied to mastered physics
- simulation as a prediction/testing environment
- measurement and experiment workflows
- project/build records that persist with the learner

### Phase 5 — Builder ecosystem
- hardware projects and constrained-resource pathways
- safe real-world experimentation
- reusable project templates and instrumentation
- eventually hardware marketplace/integration capabilities

### Phase 6 — Scale and intelligence
- stronger model/tool integrations
- semantic learner memory built on durable structured state
- reliability, security and observability hardening
- production deployment and multi-device resilience

## Drift test

Before merging a feature, ask:

- Does it improve understanding, evidence, progression, experimentation or building?
- Does it preserve physics as the spine?
- Does it use durable learner state?
- Does it work for both an early learner and an advanced entrant?
- Is the behavior real rather than mocked?
- Can we test the important behavior deterministically?
- Are we building a capability we can actually support now?

If the answer is no, it belongs in the backlog or should be rejected.
