import { getConcept } from '../curriculum.js';
import { diagnoseReasoning } from '../diagnostics.js';
import type { LearningEngine, LearnerSnapshot, AttemptInput, RemediationInput, ReviewInput } from '../learning-engine.js';

/** Application boundary used by HTTP adapters. No framework, database or LLM leaks into it. */
export class VitaService {
  constructor(private readonly learning: LearningEngine) {}

  start(studentId: number): LearnerSnapshot {
    return this.learning.start(studentId);
  }

  snapshot(studentId: number): LearnerSnapshot {
    return this.learning.snapshot(studentId);
  }

  nextIntervention(studentId: number) {
    return this.learning.nextIntervention(studentId);
  }

  submitAttempt(studentId: number, conceptId: string, input: AttemptInput): LearnerSnapshot {
    getConcept(conceptId);
    return this.learning.recordStructuredAttempt(studentId, conceptId, input);
  }

  diagnose(conceptId: string, reasoning: string) {
    getConcept(conceptId);
    return diagnoseReasoning(conceptId, reasoning);
  }

  submitRemediation(studentId: number, interventionId: number, input: RemediationInput) {
    return this.learning.submitRemediationAttempt(studentId, interventionId, input);
  }

  nextReview(studentId: number) {
    return this.learning.nextReview(studentId);
  }

  submitReview(studentId: number, input: ReviewInput) {
    return this.learning.submitReviewAttempt(studentId, input);
  }

  timeline(studentId: number) {
    return this.learning.timeline(studentId);
  }
}
