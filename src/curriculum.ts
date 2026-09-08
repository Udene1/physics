export type Domain = 'mechanics' | 'thermal_physics' | 'waves_optics' | 'electricity_magnetism' | 'modern_physics' | 'mathematics' | 'engineering';
export type ModernSpecialization = 'relativity' | 'quantum' | 'atomic_nuclear';

export interface Concept {
  id: string;
  name: string;
  domain: Domain;
  prerequisites: string[];
  mathDependencies: string[];
  description: string;
}

const concepts: Concept[] = [
  { id:'measurement', name:'Measurement & physical quantities', domain:'mechanics', prerequisites:[], mathDependencies:['arithmetic'], description:'Units, dimensions, estimation, uncertainty and reading physical measurements.' },
  { id:'motion', name:'Motion', domain:'mechanics', prerequisites:['measurement'], mathDependencies:['arithmetic','graphs'], description:'Position, velocity, acceleration and motion as relationships between measurable quantities.' },
  { id:'forces', name:'Forces & Newtonian dynamics', domain:'mechanics', prerequisites:['motion'], mathDependencies:['algebra','vectors'], description:'Interactions, free-body models, Newton’s laws and prediction of motion.' },
  { id:'energy', name:'Energy & work', domain:'mechanics', prerequisites:['motion','forces'], mathDependencies:['algebra'], description:'Work, kinetic and potential energy, conservation and power.' },
  { id:'momentum', name:'Momentum & collisions', domain:'mechanics', prerequisites:['motion','forces'], mathDependencies:['algebra','vectors'], description:'Momentum, impulse, conservation and collision models.' },
  { id:'rotation', name:'Rotation', domain:'mechanics', prerequisites:['forces','energy'], mathDependencies:['algebra','trigonometry'], description:'Torque, angular motion, rotational energy and angular momentum.' },
  { id:'gravitation', name:'Gravitation', domain:'mechanics', prerequisites:['forces','energy'], mathDependencies:['algebra','vectors'], description:'Universal gravitation, orbits and gravitational energy.' },
  { id:'temperature_heat', name:'Temperature & heat', domain:'thermal_physics', prerequisites:['measurement','energy'], mathDependencies:['algebra'], description:'Temperature, thermal energy, heat transfer and microscopic interpretation.' },
  { id:'thermodynamics', name:'Thermodynamics', domain:'thermal_physics', prerequisites:['temperature_heat'], mathDependencies:['algebra','graphs'], description:'Systems, state variables, laws of thermodynamics and engines.' },
  { id:'statistical_physics', name:'Statistical ideas', domain:'thermal_physics', prerequisites:['thermodynamics'], mathDependencies:['algebra','functions'], description:'Macroscopic behavior emerging from microscopic states and probability.' },
  { id:'oscillations', name:'Oscillations', domain:'waves_optics', prerequisites:['motion','energy'], mathDependencies:['trigonometry','functions'], description:'Periodic motion, phase, frequency, amplitude and simple harmonic motion.' },
  { id:'waves', name:'Waves', domain:'waves_optics', prerequisites:['oscillations'], mathDependencies:['trigonometry','graphs'], description:'Wave propagation, superposition, wavelength, frequency and energy transport.' },
  { id:'sound', name:'Sound', domain:'waves_optics', prerequisites:['waves'], mathDependencies:['algebra'], description:'Sound as a mechanical wave, resonance and acoustic behavior.' },
  { id:'light', name:'Light & optics', domain:'waves_optics', prerequisites:['waves'], mathDependencies:['geometry','trigonometry'], description:'Rays, lenses, mirrors and wave behavior of light.' },
  { id:'interference', name:'Interference & diffraction', domain:'waves_optics', prerequisites:['light','waves'], mathDependencies:['trigonometry','functions'], description:'Superposition, interference, diffraction and wave-based measurement.' },
  { id:'fields', name:'Fields', domain:'electricity_magnetism', prerequisites:['forces','vectors'], mathDependencies:['vectors','functions'], description:'Electric and magnetic fields as physical entities that predict interactions.' },
  { id:'circuits', name:'Circuits', domain:'electricity_magnetism', prerequisites:['fields','energy'], mathDependencies:['algebra','graphs'], description:'Charge, voltage, current, resistance, power and circuit models.' },
  { id:'electromagnetism', name:'Electromagnetism', domain:'electricity_magnetism', prerequisites:['fields','circuits'], mathDependencies:['vectors','calculus'], description:'Changing fields, induction, electromagnetic waves and unified field thinking.' },
  { id:'maxwell', name:'Maxwell-level field theory', domain:'electricity_magnetism', prerequisites:['electromagnetism'], mathDependencies:['vectors','calculus'], description:'The field equations, their structure and what they predict about electromagnetic reality.' },
  { id:'relativity', name:'Relativity', domain:'modern_physics', prerequisites:['motion','fields'], mathDependencies:['algebra','functions'], description:'Spacetime, invariance, relativity of simultaneity and relativistic dynamics.' },
  { id:'quantum', name:'Quantum physics', domain:'modern_physics', prerequisites:['waves','fields'], mathDependencies:['algebra','functions'], description:'States, measurement, probability amplitudes and the quantum description of nature.' },
  { id:'atomic_nuclear', name:'Atomic & nuclear physics', domain:'modern_physics', prerequisites:['quantum'], mathDependencies:['algebra','functions'], description:'Atomic structure, spectra, nuclei, radioactivity and nuclear processes.' },
  { id:'engineering_design', name:'Engineering design', domain:'engineering', prerequisites:['energy','circuits','waves'], mathDependencies:['algebra','geometry'], description:'Turn physical understanding into measured, testable designs and prototypes.' },
];

const math: Concept[] = [
  { id:'arithmetic', name:'Arithmetic', domain:'mathematics', prerequisites:[], mathDependencies:[], description:'Quantities, operations, estimation and numerical fluency.' },
  { id:'fractions', name:'Fractions & proportional reasoning', domain:'mathematics', prerequisites:['arithmetic'], mathDependencies:[], description:'Fractions, ratios, scaling and proportional relationships.' },
  { id:'algebra', name:'Algebra', domain:'mathematics', prerequisites:['arithmetic','fractions'], mathDependencies:[], description:'Symbols, equations, rearrangement and relationships between quantities.' },
  { id:'geometry', name:'Geometry', domain:'mathematics', prerequisites:['arithmetic'], mathDependencies:[], description:'Shape, space, measurement and geometric relationships.' },
  { id:'graphs', name:'Graphs', domain:'mathematics', prerequisites:['algebra'], mathDependencies:[], description:'Reading and constructing graphs as representations of relationships.' },
  { id:'trigonometry', name:'Trigonometry', domain:'mathematics', prerequisites:['geometry','algebra'], mathDependencies:[], description:'Angles, triangles and periodic relationships.' },
  { id:'vectors', name:'Vectors', domain:'mathematics', prerequisites:['geometry','algebra'], mathDependencies:[], description:'Magnitude, direction, components and vector operations.' },
  { id:'functions', name:'Functions', domain:'mathematics', prerequisites:['algebra','graphs'], mathDependencies:[], description:'Inputs, outputs, transformations and mathematical models.' },
  { id:'calculus', name:'Calculus', domain:'mathematics', prerequisites:['functions','algebra','graphs'], mathDependencies:[], description:'Change, accumulation, derivatives and integrals used when physics requires them.' },
];

export const CURRICULUM: readonly Concept[] = [...math, ...concepts];
const byId = new Map(CURRICULUM.map(c => [c.id, c]));

export function getConcept(id: string): Concept {
  const concept = byId.get(id);
  if (!concept) throw new Error(`Unknown concept: ${id}`);
  return concept;
}

export function validateCurriculum(): void {
  for (const concept of CURRICULUM) {
    for (const prerequisite of concept.prerequisites) getConcept(prerequisite);
    for (const dependency of concept.mathDependencies) getConcept(dependency);
  }
  const visiting = new Set<string>();
  const visited = new Set<string>();
  const visit = (id: string): void => {
    if (visiting.has(id)) throw new Error(`Curriculum cycle detected at ${id}`);
    if (visited.has(id)) return;
    visiting.add(id);
    for (const p of getConcept(id).prerequisites) visit(p);
    visiting.delete(id);
    visited.add(id);
  };
  for (const c of CURRICULUM) visit(c.id);
}

export function missingRequirements(mastery: Record<string, number>, id: string, threshold = 70): string[] {
  const concept = getConcept(id);
  return [...concept.prerequisites, ...concept.mathDependencies].filter(dep => (mastery[dep] ?? 0) < threshold);
}

export function learningFrontier(mastery: Record<string, number>, threshold = 70): Concept[] {
  return CURRICULUM.filter(c => (mastery[c.id] ?? 0) < 100 && missingRequirements(mastery, c.id, threshold).length === 0);
}

export function chooseNextPhysicsConcept(mastery: Record<string, number>): Concept | undefined {
  const frontier = learningFrontier(mastery).filter(c => c.domain !== 'mathematics');
  return frontier.find(c => c.domain === 'mechanics') ?? frontier.find(c => c.domain !== 'engineering') ?? frontier[0];
}
