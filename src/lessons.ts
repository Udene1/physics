import { getConcept } from './curriculum.js';

export interface LessonStep {
  id: string;
  type: 'observe' | 'model' | 'math' | 'predict' | 'test' | 'explain';
  prompt: string;
  expectedEvidence: string[];
}

export interface PhysicsLesson {
  id: string;
  conceptId: string;
  title: string;
  goal: string;
  difficulty: number;
  steps: LessonStep[];
}

export const PHYSICS_LESSONS: readonly PhysicsLesson[] = [
  {
    id: 'motion-from-change', conceptId: 'motion', title: 'Motion is change',
    goal: 'Build motion models from position and time before introducing formulas.', difficulty: 1,
    steps: [
      { id: 'observe', type: 'observe', prompt: 'Describe what changes when an object moves and what could be measured.', expectedEvidence: ['position', 'time'] },
      { id: 'model', type: 'model', prompt: 'Explain how two measurements can describe how quickly position changes.', expectedEvidence: ['change', 'position', 'time'] },
      { id: 'math', type: 'math', prompt: 'Write a relationship for average speed using distance and elapsed time.', expectedEvidence: ['distance', 'time', 'divide'] },
      { id: 'predict', type: 'predict', prompt: 'Predict the speed of an object travelling 20 m in 4 s.', expectedEvidence: ['5'] },
      { id: 'test', type: 'test', prompt: 'Compare your prediction with the measured journey and explain any difference.', expectedEvidence: ['measurement', 'prediction'] },
      { id: 'explain', type: 'explain', prompt: 'Explain why average speed describes a whole journey rather than one instant.', expectedEvidence: ['average', 'journey'] },
    ],
  },
  {
    id: 'forces-as-interactions', conceptId: 'forces', title: 'Forces change motion',
    goal: 'Use interaction models and net force to predict acceleration.', difficulty: 2,
    steps: [
      { id: 'observe', type: 'observe', prompt: 'Identify the interactions acting on a moving object.', expectedEvidence: ['force', 'interaction'] },
      { id: 'model', type: 'model', prompt: 'Explain why opposing forces combine into a net force.', expectedEvidence: ['net', 'opposite'] },
      { id: 'math', type: 'math', prompt: 'Relate net force, mass and acceleration with an equation.', expectedEvidence: ['F = ma', 'force', 'mass', 'acceleration'] },
      { id: 'predict', type: 'predict', prompt: 'Predict the acceleration when 10 N acts on a 2 kg object.', expectedEvidence: ['5', 'm/s'] },
      { id: 'test', type: 'test', prompt: 'Check whether the predicted acceleration points with or against the net force.', expectedEvidence: ['direction', 'net force'] },
      { id: 'explain', type: 'explain', prompt: 'Explain what would change if the mass doubled while net force stayed fixed.', expectedEvidence: ['mass', 'acceleration'] },
    ],
  },
];

const byId = new Map(PHYSICS_LESSONS.map(lesson => [lesson.id, lesson]));

export function getLesson(id: string): PhysicsLesson {
  const lesson = byId.get(id);
  if (!lesson) throw new Error(`Unknown lesson: ${id}`);
  getConcept(lesson.conceptId);
  return lesson;
}

export function lessonsForConcept(conceptId: string): PhysicsLesson[] {
  getConcept(conceptId);
  return PHYSICS_LESSONS.filter(lesson => lesson.conceptId === conceptId);
}
