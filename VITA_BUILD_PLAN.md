# Vita Build Plan

> Product build roadmap and live progress tracker. Update this file as milestones are completed. The goal is not to ship a demo quickly; it is to build a defensible adaptive learning product that can be piloted by a real school.

## Target timeline

**~4 weeks:** compelling school-facing product suitable for initial conversations and demonstrations.

**~6–8 weeks:** strong pilot-ready product with the core adaptive loop, teacher intelligence, reliability, privacy, and polished UX in place.

The schedule is a guide, not permission to ship unfinished foundations. A milestone is complete only when the underlying behavior is real, tested, and integrated.

---

## Product north star

Vita helps students learn physics by detecting *why* their reasoning fails and systematically repairing the underlying misconception.

For schools, Vita should answer:

- **Who needs attention?**
- **What misconception is blocking them?**
- **What intervention should happen next?**
- **Did the intervention actually repair the reasoning?**
- **Did the student retain and transfer the concept later?**

The long-term product is learning intelligence, not simply an AI tutor.

---

# Phase 1 — Adaptive learning foundation

**Target: Week 1**

### Goal
Build the durable learning engine and evidence model before adding more surface-level features.

### Work

- [x] Define misconception → intervention → remediation → review loop.
- [x] Define structured reasoning diagnostics.
- [x] Detect misconceptions from reasoning, not only final answers.
- [x] Define positive evidence required before a misconception can be considered repaired.
- [x] Add targeted discrimination and transfer stages.
- [x] Add spaced review policy based on demonstrated performance.
- [x] Establish PostgreSQL as the canonical database from day one.
- [x] Establish real PostgreSQL migration infrastructure.
- [x] Establish atomic evidence + mastery persistence.
- [x] Establish atomic remediation persistence.
- [x] Establish atomic review persistence.
- [x] Add immutable learning-event ledger.
- [x] Make learner timeline reconstructable from immutable events.
- [x] Add real PostgreSQL integration tests for critical persistence behavior.
- [ ] Complete end-to-end verification of every adaptive state transition.
- [ ] Remove remaining ambiguity between legacy SQLite engine and canonical PostgreSQL engine.

### Definition of done
A real student attempt can move through the adaptive loop without mock state, and a failed transaction cannot leave Vita believing something happened when it did not.

---

# Phase 2 — Structured practice and diagnostic loop

**Target: Week 1–2**

### Goal
Make the adaptive loop genuinely useful to a learner.

### Work

- [x] Build real structured physics problem catalog.
- [x] Add server-side answer specifications.
- [x] Add reasoning checkpoints.
- [x] Evaluate reasoning + answer together.
- [x] Generate targeted remediation problems from identified misconceptions.
- [x] Persist remediation evidence.
- [x] Support discrimination → transfer → repair flow.
- [x] Schedule later review after demonstrated repair.
- [ ] Expand problem coverage across the initial Mechanics curriculum.
- [ ] Add robust transfer-problem coverage for each major misconception.
- [ ] Add stronger unit/equation/assumption diagnostics across problem types.
- [ ] Verify every remediation path has a meaningful failure path and recovery path.
- [ ] Ensure generated learning artifacts are captured with provenance.
- [ ] Link presented/attempted/validated artifacts to the resulting learner evidence.

### Definition of done
Vita can observe a student's reasoning, identify a defensible misconception, repair the smallest prerequisite needed, test transfer, and schedule review based on actual evidence.

---

# Phase 3 — Learning data, provenance and auditability

**Target: Week 2**

### Goal
Make every important learning decision explainable and preserve high-value longitudinal data without treating AI output as truth.

### Work

- [x] Immutable learning event ledger.
- [x] Transaction-bound event writes.
- [x] Append-only protection for learning events.
- [x] Generated learning artifact provenance schema.
- [x] Artifact validation/training eligibility fields.
- [x] Artifact usage linkage to learner evidence.
- [x] Cross-learner attribution protection.
- [ ] Integrate artifact provenance into all actual generation paths.
- [ ] Record model/provider/version and prompt-template version consistently.
- [ ] Record curriculum/content version consistently.
- [ ] Separate raw learner data, generated content and derived diagnostic signals.
- [ ] Define retention classes and expiration behavior.
- [ ] Define learner/school deletion and redaction semantics.
- [ ] Keep training eligibility opt-in rather than default.
- [ ] Add tests proving failed domain transactions do not leave orphan learning events or artifact usage.

### Definition of done
For any meaningful learning outcome we can reconstruct what was presented, what the learner reasoned, how Vita evaluated it, what state changed, and which content/model/version participated.

---

# Phase 4 — Teacher / classroom learning intelligence

**Target: Week 2–3**

### Goal
Turn Vita from an individual tutor into something a school has a reason to adopt.

### Work

- [x] Establish protected teacher learner-intelligence API boundary.
- [x] Expose mastery, misconceptions, confidence/evidence and intervention state.
- [x] Expose due reviews and recent learning evidence.
- [ ] Build teacher dashboard.
- [ ] Build class-level attention queue: who needs my attention and why.
- [ ] Show active misconception distribution across a class.
- [ ] Show intervention outcomes and repair rates.
- [ ] Show students who repeatedly fail the same prerequisite.
- [ ] Show students ready to move forward.
- [ ] Add curriculum-aware class progress.
- [ ] Add privacy-safe aggregation and teacher authorization boundaries.
- [ ] Add intervention effectiveness reporting.

### Definition of done
A teacher can open Vita and immediately understand which students are blocked, why they are blocked, what Vita has done, and whether it worked.

---

# Phase 5 — School intelligence and curriculum layer

**Target: Week 3–4**

### Goal
Create the school-level value proposition beyond tutoring.

### Work

- [ ] Map curriculum concepts to prerequisites.
- [ ] Map concepts to known misconception families.
- [ ] Show prerequisite bottlenecks across a class/school.
- [ ] Identify recurring misconception patterns at cohort level.
- [ ] Show intervention effectiveness by misconception/intervention type.
- [ ] Produce privacy-safe teacher/school reports.
- [ ] Establish a school-specific learning profile without exposing unnecessary student data.
- [ ] Add pilot/research instrumentation for validating learning outcomes.

### Definition of done
A school can use Vita's aggregated intelligence to understand *where learning is breaking down*, not merely see individual quiz scores.

---

# Phase 6 — Backend architecture migration

**Target: Week 4–5**

### Goal
Finish the transition from the legacy Python-centered architecture to the canonical application boundary without breaking the existing product.

### Target architecture

```text
Vita UI
  ↓
HTTP/API adapter
  ↓
Vita Application
  ↓
Learning Engine
  ↓
PostgreSQL

LLMs → Model Gateway → Learning Engine
```

### Work

- [x] Establish TypeScript adaptive engine boundary.
- [x] Establish PostgreSQL application infrastructure.
- [x] Establish replaceable model gateway boundary.
- [x] Keep Flask as an incremental migration bridge.
- [ ] Move all canonical adaptive flows behind the PostgreSQL application boundary.
- [ ] Integrate generated artifact provenance into the model/application boundary.
- [ ] Migrate remaining Flask adaptive routes away from legacy bridge behavior.
- [ ] Preserve legacy chat capabilities only where they have demonstrated product value.
- [ ] Retire obsolete Python learner-state/application logic.
- [ ] Remove SQLite persistence once no production path depends on it.
- [ ] Remove duplicated routing/orchestration.
- [ ] Keep Python only where there is a demonstrated technical reason to keep it.

### Definition of done
The Python/Flask layer is no longer the owner of learner state. PostgreSQL + TypeScript application/learning engine is authoritative.

---

# Phase 7 — Next.js / TypeScript product UI

**Target: Week 5–6**

### Goal
Incrementally replace the legacy Flask-rendered UI with a modern product interface without prematurely ripping out working infrastructure.

### Work

- [ ] Establish Next.js + TypeScript frontend shell.
- [ ] Build learner home / current journey view.
- [ ] Build misconception/intervention explanation UI.
- [ ] Build practice and reasoning capture UI.
- [ ] Build remediation and transfer UI.
- [ ] Build review UI.
- [ ] Build teacher dashboard UI.
- [ ] Build class attention queue.
- [ ] Build progress/timeline views from canonical API.
- [ ] Move authentication/session handling to the new frontend boundary.
- [ ] Remove Flask UI routes after equivalent functionality is proven.
- [ ] Remove Flask only after the migration is complete and tested.

### Definition of done
The main learner and teacher experiences are served by the modern frontend while the canonical backend remains stable underneath.

---

# Phase 8 — Reliability, security, privacy and pilot hardening

**Target: Week 5–7**

### Goal
Make Vita safe and reliable enough for real students and a school pilot.

### Work

- [ ] End-to-end PostgreSQL integration suite for core learning flows.
- [ ] Concurrency tests for all state-consuming operations.
- [ ] Authentication and authorization hardening.
- [ ] Teacher/student data isolation tests.
- [ ] Privacy and retention controls.
- [ ] Auditability of important teacher/admin actions.
- [ ] Rate limiting and abuse controls.
- [ ] Failure/retry behavior for model-provider outages.
- [ ] No silent fallback to fake/mock learning state.
- [ ] Observability for learning-engine failures and latency.
- [ ] Production migration and rollback procedures.
- [ ] Backup/restore verification for PostgreSQL.
- [ ] Security review of externally exposed APIs.

### Definition of done
A real school can use Vita without the system making unverifiable claims about learning state or exposing one learner's data to another.

---

# Phase 9 — Pilot UX, onboarding and validation

**Target: Week 6–8**

### Goal
Make the product easy enough to put in front of a real Nigerian school and measure whether it works.

### Work

- [ ] Student onboarding and diagnostic flow.
- [ ] Teacher onboarding.
- [ ] School/class setup.
- [ ] Clear student journey: “You are here / this is blocking you / here is why / prove the repair / now you're ready.”
- [ ] Instrument activation and completion funnels.
- [ ] Define pilot learning metrics.
- [ ] Define teacher-value metrics.
- [ ] Build pilot reports.
- [ ] Run internal end-to-end pilot.
- [ ] Recruit first school/pilot partner.
- [ ] Collect teacher and student feedback.
- [ ] Measure misconception repair and later retention/transfer.
- [ ] Iterate based on evidence rather than adding features for their own sake.

### Definition of done
Vita is ready for a controlled real-world school pilot with measurable learning and teacher outcomes.

---

# Current status — 11 September 2026

## Overall assessment

**Foundational adaptive architecture: substantially built.**

**Pilot-ready product: not yet complete.**

The highest-priority remaining work is no longer basic database plumbing. It is completing the end-to-end adaptive loop, integrating provenance into real generation paths, finishing teacher/classroom intelligence, and then migrating the product UI incrementally.

## Recently completed

- PostgreSQL-first persistence.
- Forward-only migration runner.
- Atomic evidence/mastery writes.
- Atomic remediation outcomes.
- Atomic review outcomes.
- Centralized repair and spaced-review policy.
- Immutable learning-event ledger.
- Event-sourced PostgreSQL learner timeline.
- Append-only protection for learning events.
- Real PostgreSQL integration tests for rollback and concurrency-sensitive behavior.
- Learning artifact provenance and retention metadata.
- Artifact-to-evidence usage linkage.
- Cross-learner artifact attribution protection.
- Protected teacher learning-intelligence API boundary.
- Real structured physics practice and reasoning diagnostics.

## Immediate next sequence

1. Get CI fully green on the latest commits.
2. Finish event-ledger coverage for every meaningful adaptive state transition.
3. Verify review/intervention concurrency and consumption semantics end-to-end.
4. Integrate artifact provenance into actual model-generated problem/explanation paths.
5. Finish the complete misconception → intervention → remediation → transfer → repair → review journey.
6. Build the first teacher/classroom intelligence dashboard.
7. Complete privacy/retention/deletion boundaries.
8. Continue the Flask → API → Next.js migration incrementally.
9. Harden for the first real school pilot.

---

# Build discipline

These rules govern the roadmap:

1. **No mocks for core learning behavior.** Use real PostgreSQL, real persistence and real evaluation.
2. **Do not call something complete because the UI exists.** The underlying state transition must work.
3. **Do not make AI the source of truth.** Learner evidence and deterministic/domain evaluation own learning state.
4. **Do not rewrite merely because the old code is uncomfortable.** Rewrite when the architecture is demonstrably wrong for the product.
5. **Do not rip Flask out prematurely.** Migrate capability-by-capability.
6. **Do not retain Python merely because it already exists.** Keep it only when it provides a real technical advantage.
7. **Every important state transition must be transactional.**
8. **Every important historical claim must be reconstructable from durable evidence/events.**
9. **Training eligibility is opt-in.** Generated content and learner data are not automatically training data.
10. **Commit substantial work frequently.** Preserve progress and make architectural changes auditable.
11. **CI must be green before declaring a milestone complete.**
12. **Prefer evidence over feature count.** The product improves when we can prove that a learner understood something, not when we add more screens.

---

# Long-term expansion after the physics pilot

Once the physics learning loop and school intelligence are validated:

- Expand deeper across Mechanics and the rest of the physics curriculum.
- Add Mathematics as a prerequisite/diagnostic layer.
- Extend the learning-intelligence architecture to Chemistry and other subjects.
- Use accumulated learning evidence to discover which interventions actually repair which misconceptions.
- Build proprietary learning intelligence from validated outcomes rather than from raw AI-generated content alone.

**The immediate objective remains simple: make Vita good enough that a real school has a reason to use it.**
