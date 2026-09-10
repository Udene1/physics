import type { Pool } from 'pg';

export type LearningEvent = {
  studentId: number;
  eventType: string;
  aggregateType: string;
  aggregateId?: string | null;
  conceptId?: string | null;
  payload?: Record<string, unknown>;
};

export class LearningEventStore {
  constructor(private readonly pool: Pool) {}

  async append(event: LearningEvent): Promise<number> {
    const result = await this.pool.query(
      `INSERT INTO learning_events
        (student_id, event_type, aggregate_type, aggregate_id, concept_id, payload)
       VALUES ($1, $2, $3, $4, $5, $6::jsonb)
       RETURNING id`,
      [
        event.studentId,
        event.eventType,
        event.aggregateType,
        event.aggregateId ?? null,
        event.conceptId ?? null,
        JSON.stringify(event.payload ?? {}),
      ],
    );
    return Number(result.rows[0].id);
  }

  async list(studentId: number, limit = 100) {
    if (!Number.isInteger(limit) || limit < 1 || limit > 500) {
      throw new Error('event limit must be an integer between 1 and 500');
    }
    const result = await this.pool.query(
      `SELECT id, event_type, aggregate_type, aggregate_id, concept_id, payload, created_at
       FROM learning_events
       WHERE student_id = $1
       ORDER BY created_at DESC, id DESC
       LIMIT $2`,
      [studentId, limit],
    );
    return result.rows.map((row) => ({
      id: Number(row.id),
      eventType: String(row.event_type),
      aggregateType: String(row.aggregate_type),
      aggregateId: row.aggregate_id == null ? null : String(row.aggregate_id),
      conceptId: row.concept_id == null ? null : String(row.concept_id),
      payload: row.payload as Record<string, unknown>,
      createdAt: new Date(String(row.created_at)).toISOString(),
    }));
  }
}
