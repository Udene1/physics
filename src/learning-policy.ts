export const REPAIR_POLICY = {
  minimumPositiveEvidence: 2,
  maximumConfidenceForResolution: 30,
} as const;

export interface RepairEvidenceState {
  positiveEvidence: number;
  confidence: number;
}

export function hasDemonstratedRepair(state: RepairEvidenceState | undefined): boolean {
  return state !== undefined
    && state.positiveEvidence >= REPAIR_POLICY.minimumPositiveEvidence
    && state.confidence <= REPAIR_POLICY.maximumConfidenceForResolution;
}

export interface ReviewScheduleState {
  intervalDays: number;
  streak: number;
  lastScore?: number | null;
}

export interface ReviewSchedule {
  intervalDays: number;
  streak: number;
  dueAt: Date;
}

export function calculateReviewSchedule(
  score: number,
  previous: Partial<ReviewScheduleState> | undefined,
  referenceTime: Date,
): ReviewSchedule {
  const strong = score >= 0.8;
  const streak = strong ? Number(previous?.streak ?? 0) + 1 : 0;
  const previousInterval = Number(previous?.intervalDays ?? 0);
  const intervalDays = strong
    ? Math.min(90, previousInterval === 0 ? 1 : previousInterval * (streak >= 3 ? 3 : 2))
    : 1;
  return {
    intervalDays,
    streak,
    dueAt: new Date(referenceTime.getTime() + intervalDays * 86_400_000),
  };
}
