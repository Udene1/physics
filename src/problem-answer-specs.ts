import type { ProblemAnswerSpec } from './problem-answer-spec.js';

const concept = (id: string, ...patterns: RegExp[]): ProblemAnswerSpec['criteria'][number] => ({ id, kind: 'concept', patterns });
const numeric = (id: string, expected: number, unit?: string, tolerance = 0, direction?: string): ProblemAnswerSpec['criteria'][number] => ({ id, kind: 'numeric', expected, tolerance, ...(unit ? { unit } : {}), ...(direction ? { direction } : {}) });

export const ANSWER_SPECS: Readonly<Record<string, ProblemAnswerSpec>> = {
  'force-motion-discrimination-1': {criteria:[numeric('net-force',0,'N'),concept('causal-model',/motion.*not.*require.*force/i,/does not.*need.*force/i,/not.*need.*force.*(?:sustain|maintain)/i,/not.*(?:needed|required).*to.*(?:sustain|maintain).*(?:motion|movement|(?:constant\s+)?velocity)/i,/(?:constant\s+velocity|constant\s+speed).*does not.*(?:require|need).*force/i,/(?:constant\s+velocity|constant\s+speed).*(?:requires|needs)\s+no\s+(?:net\s+)?force/i,/no\s+(?:net\s+)?force.*(?:needed|required).*to.*(?:keep|maintain|sustain).*(?:moving|motion|movement|constant\s+velocity)/i,/(?:force|net force).*changes?.*velocity.*(?:not|rather than).*sustain/i,/(?:force|net force).*changes?.*velocity.*through acceleration/i)]},
  'force-motion-transfer-1': {criteria:[numeric('acceleration',2,'m/s²',0,'east'),numeric('final-velocity',7,'m/s',0,'east')]},
  'heat-temperature-discrimination-1': {criteria:[concept('temperature-distinction',/temperature.*not.*(?:heat|amount)/i,/not.*(?:heat|amount).*temperature/i),concept('heat-transfer',/(?:heat|energy).*transfer/i)]},
  'heat-temperature-transfer-1': {criteria:[concept('thermal-state',/final.*thermal state/i,/temperature.*thermal state/i),concept('energy-transfer',/energy.*transfer.*hotter.*cooler/i,/heat.*transfer/i)]},
  'energy-force-discrimination-1': {criteria:[numeric('work',20,'J'),concept('quantity-distinction',/force.*work.*different/i,/force.*not.*(?:same|equal).*work/i)]},
  'energy-force-transfer-1': {criteria:[numeric('force',10,'N'),numeric('energy-transfer',30,'J'),concept('unit-distinction',/N.*J.*different/i,/different.*units/i)]},
  'direction-scalar-discrimination-1': {criteria:[numeric('net-force',4,'N',0,'east'),concept('vector-treatment',/opposite.*direction/i,/subtract/i)]},
  'direction-scalar-transfer-1': {criteria:[numeric('magnitude',5,'N'),concept('direction',/north.*east/i,/northeast/i)]},
  'ratio-additive-discrimination-1': {criteria:[numeric('flour',12,'cups'),concept('multiplicative-scale',/multiply|multiplicative|scale/i)]},
  'ratio-additive-transfer-1': {criteria:[numeric('distance',1.5,'km',0.001),concept('multiplicative-scale',/multiply|multiplicative|scale/i)]},
  'forces-review-1': {criteria:[numeric('acceleration',2,'m/s²',0,'west'),numeric('final-velocity',0,'m/s')]},
  'energy-review-1': {criteria:[numeric('work',50,'J'),concept('quantity-distinction',/N.*(?:force|work).*J/i,/force.*(?:not|while).*work/i,/force.*work.*different.*(?:quantity|units)/i,/N\s+and\s+J.*different/i,/newtons?.*joules?.*different/i)]},
  'temperature-review-1': {criteria:[concept('thermal-state',/thermal state/i,/final.*temperature/i),concept('heat-transfer',/heat.*(?:energy )?transfer/i,/energy.*transfer/i)]},
  'vectors-review-1': {criteria:[numeric('magnitude',13,'N'),concept('direction',/north.*east/i,/northeast/i)]},
  'ratio-review-1': {criteria:[numeric('distance',2,'km'),concept('multiplicative-scale',/multiplicative/i,/multiply/i)]},
};

export function getProblemAnswerSpec(problemId: string): ProblemAnswerSpec | undefined { return ANSWER_SPECS[problemId]; }
