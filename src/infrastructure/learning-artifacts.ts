import type { Pool, PoolClient } from 'pg';

export type LearningArtifactKind = 'lesson' | 'explanation' | 'hint' | 'problem' | 'remediation_problem' | 'review_problem' | 'teacher_summary';
export type ArtifactValidationStatus = 'unvalidated' | 'validated' | 'rejected';
export type ArtifactRetentionClass = 'standard' | 'extended' | 'restricted';
export type ArtifactUsageKind = 'presented' | 'attempted' | 'validated' | 'teacher_reviewed';

export interface GeneratedArtifactInput {
  studentId?: number | null;
  artifactKind: LearningArtifactKind;
  content: unknown;
  generationContext?: unknown;
  modelProvider?: string | null;
  modelName?: string | null;
  modelVersion?: string | null;
  promptTemplateVersion?: string | null;
  curriculumVersion?: string | null;
  validationStatus?: ArtifactValidationStatus;
  trainingEligible?: boolean;
  retentionClass?: ArtifactRetentionClass;
  expiresAt?: Date | null;
}

export interface LearningArtifact {
  id: number; studentId: number | null; artifactKind: LearningArtifactKind;
  content: unknown; generationContext: unknown; modelProvider: string | null;
  modelName: string | null; modelVersion: string | null; promptTemplateVersion: string | null;
  curriculumVersion: string | null; validationStatus: ArtifactValidationStatus;
  trainingEligible: boolean; retentionClass: ArtifactRetentionClass;
  expiresAt: string | null; deletedAt: string | null; createdAt: string;
}

const isoOrNull = (value: unknown) => value == null ? null : new Date(String(value)).toISOString();
const toArtifact = (r: Record<string, unknown>): LearningArtifact => ({
  id: Number(r.id), studentId: r.student_id == null ? null : Number(r.student_id),
  artifactKind: r.artifact_kind as LearningArtifactKind, content: r.content, generationContext: r.generation_context,
  modelProvider: r.model_provider == null ? null : String(r.model_provider), modelName: r.model_name == null ? null : String(r.model_name),
  modelVersion: r.model_version == null ? null : String(r.model_version), promptTemplateVersion: r.prompt_template_version == null ? null : String(r.prompt_template_version),
  curriculumVersion: r.curriculum_version == null ? null : String(r.curriculum_version), validationStatus: r.validation_status as ArtifactValidationStatus,
  trainingEligible: Boolean(r.training_eligible), retentionClass: r.retention_class as ArtifactRetentionClass,
  expiresAt: isoOrNull(r.expires_at), deletedAt: isoOrNull(r.deleted_at), createdAt: new Date(String(r.created_at)).toISOString(),
});

async function insertArtifact(client: PoolClient, input: GeneratedArtifactInput): Promise<LearningArtifact> {
  const r = await client.query(`INSERT INTO learning_artifacts
    (student_id,artifact_kind,content,generation_context,model_provider,model_name,model_version,prompt_template_version,curriculum_version,validation_status,training_eligible,retention_class,expires_at)
    VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13) RETURNING *`, [
      input.studentId ?? null, input.artifactKind, JSON.stringify(input.content), JSON.stringify(input.generationContext ?? {}),
      input.modelProvider ?? null, input.modelName ?? null, input.modelVersion ?? null, input.promptTemplateVersion ?? null,
      input.curriculumVersion ?? null, input.validationStatus ?? 'unvalidated', input.trainingEligible ?? false,
      input.retentionClass ?? 'standard', input.expiresAt ?? null,
    ]);
  return toArtifact(r.rows[0] as Record<string, unknown>);
}

export async function recordGeneratedArtifact(pool: Pool, input: GeneratedArtifactInput): Promise<LearningArtifact> {
  const client = await pool.connect();
  try { await client.query('BEGIN'); const value = await insertArtifact(client, input); await client.query('COMMIT'); return value; }
  catch (error) { await client.query('ROLLBACK'); throw error; } finally { client.release(); }
}

export async function recordArtifactUsage(pool: Pool, artifactId: number, usageKind: ArtifactUsageKind, studentId?: number | null, evidenceId?: number | null): Promise<number> {
  const r = await pool.query('INSERT INTO learning_artifact_usage(artifact_id,student_id,evidence_id,usage_kind) VALUES($1,$2,$3,$4) RETURNING id', [artifactId, studentId ?? null, evidenceId ?? null, usageKind]);
  return Number(r.rows[0].id);
}

export async function recordArtifactAndUsage(pool: Pool, input: GeneratedArtifactInput, usageKind: ArtifactUsageKind, evidenceId?: number | null): Promise<LearningArtifact> {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const value = await insertArtifact(client, input);
    await client.query('INSERT INTO learning_artifact_usage(artifact_id,student_id,evidence_id,usage_kind) VALUES($1,$2,$3,$4)', [value.id, input.studentId ?? null, evidenceId ?? null, usageKind]);
    await client.query('COMMIT');
    return value;
  } catch (error) { await client.query('ROLLBACK'); throw error; } finally { client.release(); }
}
