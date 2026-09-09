import type { RemediationProblem } from './interventions.js';

export type ReviewOutcome = 'retained' | 'misconception_reopened' | 'new_misconception' | 'insufficient_evidence';

export interface ReviewProblem extends RemediationProblem {
  readonly reviewConcept: string;
}

const REVIEWS: readonly ReviewProblem[] = [
  {
    id: 'forces-review-1', misconceptionCode: 'force_causes_motion', conceptId: 'forces', prerequisiteConceptId: 'motion', stage: 'transfer', reviewConcept: 'forces',
    prompt: 'A 3 kg cart moves east at 4 m/s. A 6 N net force acts west for 2 s. Find its acceleration and final velocity. Explain whether the force is needed to keep the cart moving.',
    givens: ['m = 3 kg', 'u = 4 m/s east', 'F_net = 6 N west', 't = 2 s'],
    expectedReasoning: ['Choose east as positive and represent west as negative.', 'Use F_net = ma.', 'a = -2 m/s², so acceleration is 2 m/s² west.', 'Use v = u + at to obtain v = 0 m/s.', 'The net force changes velocity; it does not merely sustain motion.'],
    checkpoints: [
      { id: 'equation', label: 'Newton law', expected: 'Use F_net = ma to determine acceleration.' },
      { id: 'direction', label: 'Direction', expected: 'West is opposite the chosen east-positive direction.' },
      { id: 'change', label: 'Motion change', expected: 'Net force changes velocity through acceleration.' },
    ],
    answer: 'a = 2 m/s² west and v = 0 m/s; the net force changes velocity rather than sustaining motion.'
  },
  {
    id: 'energy-review-1', misconceptionCode: 'energy_as_force', conceptId: 'energy', prerequisiteConceptId: 'forces', stage: 'transfer', reviewConcept: 'energy',
    prompt: 'A 20 N horizontal force moves a box 2.5 m in the direction of the force. Calculate the work done. Then explain why 20 N and 50 J cannot be treated as the same physical quantity.',
    givens: ['F = 20 N', 'd = 2.5 m', 'Force is parallel to displacement'],
    expectedReasoning: ['Force describes an interaction and is measured in newtons.', 'Use W = Fd.', 'W = 50 J.', 'Work is energy transferred through displacement and is measured in joules.'],
    checkpoints: [
      { id: 'interaction', label: 'Force', expected: 'Force describes an interaction and has units of newtons.' },
      { id: 'work', label: 'Work', expected: 'Work transfers energy through displacement.' },
      { id: 'units', label: 'Units', expected: 'Force uses N while work and energy use J.' },
    ],
    answer: 'W = 50 J; 20 N is force while 50 J is work/energy transfer.'
  },
  {
    id: 'temperature-review-1', misconceptionCode: 'heat_equals_temperature', conceptId: 'temperature_heat', prerequisiteConceptId: 'energy', stage: 'transfer', reviewConcept: 'temperature_heat',
    prompt: 'A metal spoon at 90 °C is placed in water at 20 °C. After thermal equilibrium both are 30 °C. Explain what the 30 °C represents and what heat means during this process.',
    givens: ['Spoon starts at 90 °C', 'Water starts at 20 °C', 'Final equilibrium temperature is 30 °C'],
    expectedReasoning: ['Temperature describes thermal state.', 'Energy transfers from the hotter spoon to the cooler water.', 'Heat refers to energy transferred because of a temperature difference.', '30 °C is not an amount of heat stored in either object.'],
    checkpoints: [
      { id: 'temperature', label: 'Temperature', expected: 'Temperature characterizes thermal state.' },
      { id: 'heat', label: 'Heat', expected: 'Heat is energy transferred due to a temperature difference.' },
    ],
    answer: '30 °C is the final thermal state; heat is the energy transferred from the hotter spoon to the cooler water.'
  },
  {
    id: 'vectors-review-1', misconceptionCode: 'direction_as_scalar', conceptId: 'forces', prerequisiteConceptId: 'vectors', stage: 'transfer', reviewConcept: 'forces',
    prompt: 'A 5 N force acts north and a 12 N force acts east. Find the magnitude and direction of the net force. Explain why 17 N is not the correct vector magnitude.',
    givens: ['5 N north', '12 N east'],
    expectedReasoning: ['Recognize perpendicular vector components.', 'Use Pythagoras: sqrt(5² + 12²) = 13 N.', 'Direction is arctan(5/12), about 22.6° north of east.', 'Direction matters because perpendicular components cannot be added as ordinary scalars.'],
    checkpoints: [
      { id: 'direction', label: 'Vector treatment', expected: 'Perpendicular directions require vector components.' },
      { id: 'result', label: 'Result', expected: 'The net force magnitude is 13 N and points northeast.' },
    ],
    answer: '13 N at about 22.6° north of east.'
  },
  {
    id: 'ratio-review-1', misconceptionCode: 'ratio_additive', conceptId: 'fractions', prerequisiteConceptId: 'arithmetic', stage: 'transfer', reviewConcept: 'fractions',
    prompt: 'A physics model uses a scale of 1:25,000. A measured distance is 8 cm. Find the real distance in kilometres and explain why the scale is applied multiplicatively.',
    givens: ['Scale = 1:25,000', 'Measured distance = 8 cm'],
    expectedReasoning: ['Treat the ratio as a multiplicative scale factor.', '8 × 25,000 = 200,000 cm.', '200,000 cm = 2 km.', 'A ratio expresses a multiplicative relationship rather than an additive offset.'],
    checkpoints: [
      { id: 'scale', label: 'Scale factor', expected: 'Multiply by the scale factor.' },
      { id: 'relationship', label: 'Ratio relationship', expected: 'A ratio expresses a multiplicative relationship.' },
    ],
    answer: '200,000 cm = 2 km.'
  }
];

export function getReviewProblem(problemId: string): ReviewProblem {
  const problem = REVIEWS.find(p => p.id === problemId);
  if (!problem) throw new Error(`Unknown review problem: ${problemId}`);
  return problem;
}

export function getReviewProblemForConcept(conceptId: string): ReviewProblem | undefined {
  return REVIEWS.find(p => p.conceptId === conceptId);
}

export function getAllReviewProblems(): readonly ReviewProblem[] { return REVIEWS; }
