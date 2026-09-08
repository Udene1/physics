import { PhysicsProblem } from './problems.js';

export interface ReasoningSignal {
  id: string;
  present: boolean;
  evidence: string;
  strength: 'strong' | 'weak' | 'missing';
}

export interface ReasoningDiagnosis {
  signals: ReasoningSignal[];
  misconceptionCodes: string[];
}

const normalize = (value: string): string => value.toLowerCase().replace(/[^a-z0-9./-]+/g, ' ').replace(/\s+/g, ' ').trim();

export function diagnoseReasoning(problem: PhysicsProblem, reasoning: string, correct: boolean): ReasoningDiagnosis {
  const text = normalize(reasoning);
  const signals = problem.reasoningCriteria.map(criteria => {
    const matches = criteria.keywords.filter(keyword => text.includes(normalize(keyword)));
    const present = matches.length > 0;
    return {
      id: criteria.id,
      present,
      evidence: present ? `Matched: ${matches.join(', ')}` : 'No supporting reasoning evidence detected',
      strength: matches.length >= 2 ? 'strong' : present ? 'weak' : 'missing',
    } as ReasoningSignal;
  });

  const misconceptionCodes = correct ? [] : signals.filter(signal => !signal.present).map(signal => `reasoning-missing:${signal.id}`);
  return { signals, misconceptionCodes };
}
