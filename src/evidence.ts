import type { LearningRepository } from './learning-repository.js';

export interface EvidenceRecord {
  id: number;
  studentId: number;
  conceptId: string;
  kind: string;
  value: number | null;
  note: string;
  createdAt: string;
}

export interface MasteryEstimate {
  conceptId: string;
  score: number;
  confidence: number;
  evidenceCount: number;
}

const KIND_WEIGHTS: Record<string, number> = {
  diagnostic: 0.8,
  placement: 0.6,
  attempt: 1,
  problem: 1.1,
  explanation: 1.2,
  transfer: 1.4,
};

export function estimateMastery(evidence: EvidenceRecord[]): MasteryEstimate[] {
  const grouped = new Map<string, EvidenceRecord[]>();
  for (const item of evidence) {
    if (item.value === null) continue;
    const list = grouped.get(item.conceptId) ?? [];
    list.push(item);
    grouped.set(item.conceptId, list);
  }
  return [...grouped.entries()].map(([conceptId, items]) => {
    const total = items.reduce((sum, item) => sum + (KIND_WEIGHTS[item.kind] ?? 1), 0);
    const weighted = items.reduce((sum, item) => sum + (item.value! * (KIND_WEIGHTS[item.kind] ?? 1)), 0);
    return {
      conceptId,
      score: Math.round((weighted / total) * 10) / 10,
      confidence: Math.round(Math.min(1, total / 5) * 100) / 100,
      evidenceCount: items.length,
    };
  }).sort((a, b) => b.score - a.score);
}

export function evidenceSummary(store: LearningRepository, studentId: number): MasteryEstimate[] {
  return estimateMastery(store.listEvidence(studentId));
}
