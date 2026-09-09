import type { RemediationProblem } from './interventions.js';
import { evaluateCriterion } from './problem-answer-spec.js';

export interface AnswerEvaluation {
  correct: boolean;
  matchedCriteria: string[];
  missingCriteria: string[];
}

type Criterion = { id:string; pattern:RegExp };

const LEGACY_CRITERIA:Record<string, readonly Criterion[]> = {
  'force-motion-discrimination-1': [{id:'zero-force',pattern:/\b0\s*(?:n|newtons?)\b/i}],
  'force-motion-transfer-1': [{id:'acceleration',pattern:/2\s*m\/s(?:\^?2|²)/i},{id:'final-velocity',pattern:/7\s*m\/s/i},{id:'east',pattern:/\beast\b/i}],
  'heat-temperature-discrimination-1': [{id:'not-heat',pattern:/temperature.*not.*(?:heat|amount)|not.*(?:heat|amount).*temperature/i}],
  'heat-temperature-transfer-1': [{id:'thermal-state',pattern:/thermal\s+state/i},{id:'energy-transfer',pattern:/(?:energy|heat).*transfer/i}],
  'energy-force-discrimination-1': [{id:'work',pattern:/\b20\s*(?:j|joules?)\b/i}],
  'energy-force-transfer-1': [{id:'force',pattern:/\b10\s*(?:n|newtons?)\b/i},{id:'energy',pattern:/\b30\s*(?:j|joules?)\b/i}],
  'direction-scalar-discrimination-1': [{id:'magnitude',pattern:/\b4\s*(?:n|newtons?)\b/i},{id:'east',pattern:/\beast\b/i}],
  'direction-scalar-transfer-1': [{id:'magnitude',pattern:/\b5\s*(?:n|newtons?)\b/i},{id:'direction',pattern:/(?:north\s+of\s+east|northeast)/i}],
  'ratio-additive-discrimination-1': [{id:'flour',pattern:/\b12\s*cups?\b/i}],
  'ratio-additive-transfer-1': [{id:'distance',pattern:/\b1\.5\s*km\b/i}],
  'forces-review-1': [{id:'acceleration',pattern:/2\s*m\/s(?:\^?2|²)/i},{id:'west',pattern:/\bwest\b/i},{id:'zero-velocity',pattern:/\b0\s*m\/s\b/i}],
  'energy-review-1': [{id:'work',pattern:/\b50\s*(?:j|joules?)\b/i}],
  'temperature-review-1': [{id:'thermal-state',pattern:/thermal\s+state/i},{id:'energy-transfer',pattern:/(?:energy|heat).*transfer/i}],
  'vectors-review-1': [{id:'magnitude',pattern:/\b13\s*(?:n|newtons?)\b/i},{id:'direction',pattern:/(?:north\s+of\s+east|northeast)/i}],
  'ratio-review-1': [{id:'distance',pattern:/\b2\s*km\b/i}],
};

export function evaluateAnswer(problem:RemediationProblem, answer:string):AnswerEvaluation {
  const spec = problem.answerSpec;
  if (spec) {
    const matched = spec.criteria.filter(c => evaluateCriterion(c, answer)).map(c => c.id);
    const missing = spec.criteria.filter(c => !matched.includes(c.id)).map(c => c.id);
    return {correct:missing.length===0, matchedCriteria:matched, missingCriteria:missing};
  }

  // Compatibility path for the existing catalog while every problem is migrated.
  const criteria=LEGACY_CRITERIA[problem.id];
  if(!criteria) return {correct:false,matchedCriteria:[],missingCriteria:['No structured answer specification exists for this problem.']};
  const matched=criteria.filter(c=>c.pattern.test(answer)).map(c=>c.id);
  const missing=criteria.filter(c=>!matched.includes(c.id)).map(c=>c.id);
  return {correct:missing.length===0,matchedCriteria:matched,missingCriteria:missing};
}
