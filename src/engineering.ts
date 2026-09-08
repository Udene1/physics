import { getConcept, missingRequirements } from './curriculum.js';

export interface EngineeringChallenge {
  id: string;
  title: string;
  description: string;
  requiredPhysics: string[];
  difficulty: number;
  deliverables: string[];
  safetyNotes: string[];
}

export const ENGINEERING_CHALLENGES: readonly EngineeringChallenge[] = [
  {
    id: 'motion-speed-meter', title: 'Build a speed measurement experiment',
    description: 'Design a repeatable way to measure an object\'s average speed using distance and time.',
    requiredPhysics: ['measurement', 'motion'], difficulty: 1,
    deliverables: ['measurement plan', 'predicted result', 'observed result', 'error explanation'],
    safetyNotes: ['Use a harmless low-speed object and a clear test area.', 'Do not place people or fragile equipment in the object\'s path.'],
  },
  {
    id: 'force-cart', title: 'Predict a cart acceleration',
    description: 'Design a simple experiment that tests how changing force or mass changes acceleration.',
    requiredPhysics: ['measurement', 'motion', 'forces'], difficulty: 2,
    deliverables: ['free-body model', 'prediction', 'measurement plan', 'comparison of prediction and observation'],
    safetyNotes: ['Use low forces and a controlled surface.', 'Do not use hazardous weights or powered machinery.'],
  },
  {
    id: 'circuit-power', title: 'Measure electrical power safely',
    description: 'Use a low-voltage educational circuit to predict and measure electrical power.',
    requiredPhysics: ['fields', 'circuits'], difficulty: 3,
    deliverables: ['circuit model', 'prediction', 'measurement table', 'explanation of discrepancies'],
    safetyNotes: ['Use battery-level or laboratory-safe low voltage only.', 'Never connect an experimental circuit directly to mains electricity.'],
  },
];

const byId = new Map(ENGINEERING_CHALLENGES.map(challenge => [challenge.id, challenge]));

export function getEngineeringChallenge(id: string): EngineeringChallenge {
  const challenge = byId.get(id);
  if (!challenge) throw new Error(`Unknown engineering challenge: ${id}`);
  challenge.requiredPhysics.forEach(getConcept);
  return challenge;
}

export function availableEngineeringChallenges(mastery: Record<string, number>): EngineeringChallenge[] {
  return ENGINEERING_CHALLENGES.filter(challenge => missingRequirements(mastery, 'engineering_design', 70).length === 0 && challenge.requiredPhysics.every(id => (mastery[id] ?? 0) >= 70));
}
