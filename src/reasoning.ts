import type { PhysicsProblem, ReasoningCriterion } from './problems.js';

export interface ReasoningSignal {
  id: string;
  present: boolean;
  evidence: string;
  strength: 'strong' | 'weak' | 'missing';
}

export interface ReasoningDiagnosis {
  signals: ReasoningSignal[];
  misconceptionCodes: string[];
  coverage: number;
  reasoningQuality: 'strong' | 'partial' | 'insufficient';
}

const normalize = (value: string): string => value.toLowerCase().replace(/[^a-z0-9./²=+-]+/g, ' ').replace(/\s+/g, ' ').trim();

function criterionMatches(criterion: ReasoningCriterion, text: string): string[] {
  return criterion.keywords.filter(keyword => text.includes(normalize(keyword)));
}

export function diagnoseReasoning(problem: PhysicsProblem, reasoning: string): ReasoningDiagnosis {
  const text = normalize(reasoning);
  const signals = problem.reasoningCriteria.map(criteria => {
    const matches = criterionMatches(criteria, text);
    const present = matches.length > 0;
    return {
      id: criteria.id,
      present,
      evidence: present ? matches.map(match => `Matched: ${match}`).join('; ') : 'No supporting reasoning evidence detected',
      strength: matches.length >= 2 ? 'strong' : present ? 'weak' : 'missing',
    } as ReasoningSignal;
  });

  const required = problem.reasoningCriteria.filter(criteria => criteria.required !== false);
  const covered = required.filter(criteria => signals.find(signal => signal.id === criteria.id)?.present).length;
  const coverage = required.length === 0 ? 1 : Math.round((covered / required.length) * 100) / 100;
  const missingCodes = problem.reasoningCriteria
    .filter(criteria => criteria.required !== false && !signals.find(signal => signal.id === criteria.id)?.present && criteria.misconceptionCode)
    .map(criteria => criteria.misconceptionCode!);

  return {
    signals,
    misconceptionCodes: missingCodes,
    coverage,
    reasoningQuality: coverage >= 0.85 ? 'strong' : coverage >= 0.5 ? 'partial' : 'insufficient',
  };
}
