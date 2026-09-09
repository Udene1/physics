export type AnswerCriterion =
  | { id: string; kind: 'numeric'; expected: number; tolerance?: number; unit?: string; direction?: string }
  | { id: string; kind: 'concept'; patterns: readonly RegExp[] }
  | { id: string; kind: 'text'; patterns: readonly RegExp[] };

export interface ProblemAnswerSpec {
  readonly criteria: readonly AnswerCriterion[];
}

function numberMatches(text: string, expected: number, tolerance: number, unit?: string): boolean {
  const matches = [...text.matchAll(/[-+]?\d+(?:\.\d+)?/g)];
  const valueMatch = matches.some(match => Math.abs(Number(match[0]) - expected) <= tolerance);
  if (!valueMatch || !unit) return valueMatch;
  const escapedUnit = unit.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const unitPattern = unit === 'm/s²' ? /m\s*\/\s*s(?:\^?2|²)/i : new RegExp(`\\b${escapedUnit}\\b`, 'i');
  return unitPattern.test(text);
}

export function evaluateCriterion(criterion: AnswerCriterion, text: string): boolean {
  if (criterion.kind === 'numeric') {
    if (!numberMatches(text, criterion.expected, criterion.tolerance ?? 0, criterion.unit)) return false;
    return !criterion.direction || new RegExp(`\\b${criterion.direction}\\b`, 'i').test(text);
  }
  return criterion.patterns.some(pattern => pattern.test(text));
}
