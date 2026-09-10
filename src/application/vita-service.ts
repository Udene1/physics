import type { PostgresLearningEngine, AttemptInput, LearnerSnapshot, RemediationInput, ReviewResult, RemediationResult } from './postgres-learning-engine.js';
import { getConcept } from '../curriculum.js';
import { diagnoseReasoning } from '../diagnostics.js';

/** Framework-free application boundary for the production PostgreSQL learning engine. */
export class VitaService {
  constructor(private readonly learning: PostgresLearningEngine) {}
  async start(studentId: number): Promise<LearnerSnapshot> { return this.learning.start(studentId); }
  async snapshot(studentId: number): Promise<LearnerSnapshot> { return this.learning.snapshot(studentId); }
  async nextIntervention(studentId: number) { return this.learning.nextIntervention(studentId); }
  async submitAttempt(studentId: number, conceptId: string, input: AttemptInput): Promise<LearnerSnapshot> { getConcept(conceptId); return this.learning.recordStructuredAttempt(studentId, conceptId, input); }
  diagnose(conceptId: string, reasoning: string) { getConcept(conceptId); return diagnoseReasoning(conceptId, reasoning); }
  async submitRemediation(studentId: number, interventionId: number, input: RemediationInput): Promise<RemediationResult> { return this.learning.submitRemediationAttempt(studentId, interventionId, input); }
  async nextReview(studentId: number) { return this.learning.nextReview(studentId); }
  async submitReview(studentId: number, input: RemediationInput): Promise<ReviewResult> { return this.learning.submitReviewAttempt(studentId, input); }
  async timeline(studentId: number) { return this.learning.timeline(studentId); }
}
