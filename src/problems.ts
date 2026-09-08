export type ProblemAnswerType = 'numeric' | 'choice' | 'short_text';

export interface PhysicsProblem {
  id: string;
  conceptId: string;
  title: string;
  prompt: string;
  difficulty: number;
  answerType: ProblemAnswerType;
  answer: string;
  tolerance?: number;
  choices?: string[];
  reasoningPrompts: string[];
}

export const PHYSICS_PROBLEMS: readonly PhysicsProblem[] = [
  {
    id: 'measurement-length-unit',
    conceptId: 'measurement',
    title: 'Measure before calculating',
    prompt: 'A table is measured as 1.20 m long. Express its length in centimetres.',
    difficulty: 1,
    answerType: 'numeric',
    answer: '120',
    tolerance: 0,
    reasoningPrompts: ['What quantity are you converting?', 'What relationship between metres and centimetres did you use?'],
  },
  {
    id: 'motion-average-speed',
    conceptId: 'motion',
    title: 'Average speed from a journey',
    prompt: 'A cyclist travels 150 m in 30 s. What is the cyclist’s average speed?',
    difficulty: 1,
    answerType: 'numeric',
    answer: '5',
    tolerance: 0,
    reasoningPrompts: ['What measured quantities matter?', 'What equation connects distance, time, and average speed?', 'Why is this an average rather than an instantaneous speed?'],
  },
  {
    id: 'motion-position-change',
    conceptId: 'motion',
    title: 'Position is not distance',
    prompt: 'A student walks 10 m east and then 10 m west back to the starting point. What is the student’s displacement?',
    difficulty: 2,
    answerType: 'numeric',
    answer: '0',
    tolerance: 0,
    reasoningPrompts: ['What is the final position relative to the initial position?', 'Why is displacement different from total distance travelled?'],
  },
  {
    id: 'forces-net-force',
    conceptId: 'forces',
    title: 'Net force predicts acceleration',
    prompt: 'A 2 kg object experiences a net force of 10 N to the right. What is its acceleration?',
    difficulty: 2,
    answerType: 'numeric',
    answer: '5',
    tolerance: 0,
    reasoningPrompts: ['What physical law connects net force, mass, and acceleration?', 'What direction should the acceleration have?'],
  },
];

const byId = new Map(PHYSICS_PROBLEMS.map(problem => [problem.id, problem]));

export function getProblem(id: string): PhysicsProblem {
  const problem = byId.get(id);
  if (!problem) throw new Error(`Unknown problem: ${id}`);
  return problem;
}

export function problemsForConcept(conceptId: string): PhysicsProblem[] {
  return PHYSICS_PROBLEMS.filter(problem => problem.conceptId === conceptId);
}

export function isAnswerCorrect(problem: PhysicsProblem, answer: string): boolean {
  if (problem.answerType === 'numeric') {
    const actual = Number(answer.trim());
    const expected = Number(problem.answer);
    return Number.isFinite(actual) && Math.abs(actual - expected) <= (problem.tolerance ?? 0);
  }
  return answer.trim().toLowerCase() === problem.answer.trim().toLowerCase();
}
