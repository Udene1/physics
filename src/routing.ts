import { chooseNextPhysicsConcept, getConcept, missingRequirements } from './curriculum.js';
import type { LearningRepository } from './learning-repository.js';

export type NextActionKind = 'remediate' | 'review' | 'learn' | 'diagnose' | 'build';
export interface NextAction {
  kind: NextActionKind;
  conceptId: string | null;
  prerequisiteIds: string[];
  reason: string;
}

export function chooseNextAction(store: LearningRepository, studentId: number): NextAction {
  const mastery = store.getMastery(studentId);
  const open = store.listOpenMisconceptions(studentId);
  if (open.length) {
    const misconception = open[0]!;
    return { kind: 'remediate', conceptId: misconception.conceptId, prerequisiteIds: [], reason: `Resolve ${misconception.code} through a targeted retry.` };
  }
  const due = store.getDueReviews(studentId);
  if (due.length) {
    const review = due[0]!;
    return { kind: 'review', conceptId: review.conceptId, prerequisiteIds: [], reason: `Review ${review.conceptId} after its scheduled interval.` };
  }
  const next = chooseNextPhysicsConcept(mastery);
  if (!next) return { kind: 'build', conceptId: 'engineering_design', prerequisiteIds: [], reason: 'Physics frontier is complete; apply demonstrated knowledge to engineering.' };
  const missing = missingRequirements(mastery, next.id);
  if (missing.length) return { kind: 'diagnose', conceptId: next.id, prerequisiteIds: missing, reason: 'A prerequisite is not yet demonstrated.' };
  getConcept(next.id);
  return { kind: 'learn', conceptId: next.id, prerequisiteIds: [], reason: `Continue with ${next.name}.` };
}
