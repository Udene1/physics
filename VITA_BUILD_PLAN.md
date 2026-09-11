# Vita Build Plan

> Product build roadmap and live progress tracker. Update this file as milestones are completed. The goal is not to ship a demo quickly; it is to build a defensible adaptive learning product that can be piloted by a real school.

## Current status — 11 September 2026

**Foundational adaptive architecture: substantially built.**  
**Classroom intelligence foundation: now implemented.**  
**Pilot-ready product: not yet complete.**

### Recently completed

- PostgreSQL-first persistence and real migration infrastructure.
- Atomic evidence/mastery, remediation, and review outcomes.
- Immutable, append-only learning event ledger with transaction-bound events.
- Event-sourced learner timeline.
- Review consumption concurrency guard and real PostgreSQL concurrency test.
- Learning artifact provenance, usage linkage, attribution protection, and retention metadata.
- Structured physics practice and reasoning diagnostics.
- Protected teacher learner-intelligence API.
- Classroom roster, mastery, misconception, intervention-outcome, attention-queue, and prerequisite-bottleneck intelligence API.

### Immediate next sequence

1. Get the latest CI runs fully green and keep the branch green.
2. Complete end-to-end verification of every adaptive state transition and its event ledger.
3. Integrate artifact provenance into actual generated problem/explanation paths.
4. Finish the complete misconception → discrimination → transfer → repair → review journey with failure/recovery tests.
5. Expand Mechanics problem and transfer coverage.
6. Build the first teacher/classroom dashboard on the classroom intelligence API.
7. Add curriculum-aware prerequisite and misconception mapping.
8. Complete privacy, retention, deletion/redaction, and teacher/student isolation boundaries.
9. Continue Flask → API → Next.js incrementally; do not rip Flask out prematurely.
10. Harden for the first real school pilot.

## Product north star

Vita helps students learn physics by detecting *why* their reasoning fails and systematically repairing the underlying misconception.

For schools, Vita should answer:

- Who needs attention?
- What misconception is blocking them?
- What intervention should happen next?
- Did the intervention actually repair the reasoning?
- Did the student retain and transfer the concept later?

The long-term product is learning intelligence, not simply an AI tutor.

## Build discipline

1. No mocks for core learning behavior.
2. Learner evidence and deterministic/domain evaluation own learning state; AI is replaceable capability.
3. Every important state transition must be transactional.
4. Every historical learning claim must be reconstructable from durable evidence/events.
5. Training eligibility is opt-in.
6. Do not rip Flask out prematurely.
7. Keep Python only where it has a demonstrated technical reason to remain.
8. Commit substantial work frequently.
9. CI must be green before declaring a milestone complete.
10. Prefer evidence over feature count.

## Detailed roadmap

### Phase 1 — Adaptive learning foundation
- [x] Misconception → intervention → remediation → review loop.
- [x] Structured reasoning diagnostics.
- [x] PostgreSQL canonical state.
- [x] Atomic persistence.
- [x] Immutable event ledger.
- [x] Event-sourced timeline.
- [x] Review concurrency protection.
- [ ] End-to-end transition verification.
- [ ] Remove legacy SQLite ambiguity.

### Phase 2 — Structured practice and diagnostic loop
- [x] Real structured problem catalog.
- [x] Answer specifications and reasoning checkpoints.
- [x] Targeted remediation.
- [x] Discrimination → transfer flow.
- [x] Evidence-based repair and spaced review.
- [ ] Expand Mechanics coverage and transfer cases.
- [ ] Strengthen unit/equation/assumption diagnostics.
- [ ] Verify every remediation failure/recovery path.

### Phase 3 — Learning data, provenance and auditability
- [x] Provenance schema and validation/training eligibility fields.
- [x] Artifact usage linkage.
- [x] Cross-learner attribution protection.
- [ ] Integrate provenance into real generation paths.
- [ ] Retention/expiration behavior.
- [ ] Learner/school deletion and redaction semantics.
- [ ] Failed-transaction orphan tests.

### Phase 4 — Teacher / classroom learning intelligence
- [x] Protected teacher learner API.
- [x] Classroom roster and enrollment primitives.
- [x] Class mastery aggregation.
- [x] Active misconception distribution.
- [x] Intervention outcome and repair-rate aggregation.
- [x] Learner attention queue.
- [x] Prerequisite bottleneck signals.
- [ ] Teacher dashboard UI.
- [ ] Curriculum-aware class progress.
- [ ] Privacy-safe school aggregation.

### Phase 5 — School intelligence and curriculum layer
- [ ] Curriculum prerequisite graph.
- [ ] Concept → misconception-family mapping.
- [ ] Cohort bottleneck analysis.
- [ ] Intervention effectiveness by misconception/strategy.
- [ ] Privacy-safe school reports.
- [ ] Pilot/research outcome instrumentation.

### Phase 6 — Backend migration
- [x] TypeScript adaptive engine and PostgreSQL boundary.
- [x] Flask incremental bridge.
- [ ] Move all canonical adaptive flows behind the PostgreSQL application boundary.
- [ ] Retire obsolete Python learner-state/application logic.
- [ ] Remove SQLite after dependency audit.

### Phase 7 — Product UI
- [ ] Next.js + TypeScript shell.
- [ ] Learner journey UI.
- [ ] Practice/reasoning/remediation/review UI.
- [ ] Teacher dashboard and attention queue.
- [ ] Canonical timeline/progress views.
- [ ] Authentication/session migration.

### Phase 8 — Pilot hardening
- [ ] Full PostgreSQL E2E suite.
- [ ] Authentication/authorization isolation tests.
- [ ] Privacy and retention controls.
- [ ] Rate limiting and abuse controls.
- [ ] Model-provider failure/retry behavior.
- [ ] Observability.
- [ ] Production migration/rollback and backup/restore verification.

### Phase 9 — Pilot validation
- [ ] Student and teacher onboarding.
- [ ] School/class setup.
- [ ] Pilot metrics and reports.
- [ ] Internal pilot.
- [ ] First school partner.
- [ ] Measure repair, retention and transfer.
