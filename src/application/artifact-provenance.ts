import type { Pool } from 'pg';
import { recordGeneratedArtifact, recordArtifactUsage, type GeneratedArtifactInput, type LearningArtifact, type ArtifactUsageKind } from '../infrastructure/learning-artifacts.js';
import type { ModelResponse } from '../llm/model-gateway.js';

export interface ModelArtifactContext {
  studentId?: number | null;
  artifactKind: GeneratedArtifactInput['artifactKind'];
  generationContext?: unknown;
  promptTemplateVersion?: string | null;
  curriculumVersion?: string | null;
  validationStatus?: GeneratedArtifactInput['validationStatus'];
  trainingEligible?: boolean;
  retentionClass?: GeneratedArtifactInput['retentionClass'];
}

/** Persist a model response with its exact provider/model metadata before it is used. */
export async function persistModelArtifact(pool: Pool, response: ModelResponse, context: ModelArtifactContext): Promise<LearningArtifact> {
  return recordGeneratedArtifact(pool, {
    studentId: context.studentId ?? null,
    artifactKind: context.artifactKind,
    content: { text: response.text },
    generationContext: context.generationContext ?? {},
    modelProvider: response.provider,
    modelName: response.model,
    modelVersion: response.model,
    promptTemplateVersion: context.promptTemplateVersion ?? null,
    curriculumVersion: context.curriculumVersion ?? null,
    validationStatus: context.validationStatus ?? 'unvalidated',
    trainingEligible: context.trainingEligible ?? false,
    retentionClass: context.retentionClass ?? 'standard',
  });
}

/** Record that a generated artifact was actually used, optionally tying it to learner evidence. */
export async function recordModelArtifactUsage(pool: Pool, artifactId: number, usageKind: ArtifactUsageKind, studentId?: number | null, evidenceId?: number | null): Promise<number> {
  return recordArtifactUsage(pool, artifactId, usageKind, studentId, evidenceId);
}
