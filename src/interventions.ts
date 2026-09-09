import type { DiagnosticFinding } from './diagnostics.js';

export type InterventionStage = 'discrimination' | 'transfer';
export type InterventionStatus = 'queued' | 'active' | 'completed' | 'blocked';
export type RemediationVerdict = 'repaired' | 'still_present' | 'new_misconception' | 'insufficient_evidence';

export interface ReasoningCheckpoint { id:string; label:string; expected:string; }
export interface RemediationProblem {
  id:string; misconceptionCode:string; conceptId:string; prerequisiteConceptId:string; stage:InterventionStage;
  prompt:string; givens:readonly string[]; expectedReasoning:readonly string[]; checkpoints:readonly ReasoningCheckpoint[]; answer:string;
}
export interface InterventionPlan { misconceptionCode:string; strategy:string; prerequisiteConceptId:string; problems:readonly RemediationProblem[]; }

const PROBLEMS: readonly RemediationProblem[] = [
  { id:'force-motion-discrimination-1', misconceptionCode:'force_causes_motion', conceptId:'forces', prerequisiteConceptId:'motion', stage:'discrimination',
    prompt:'A hockey puck slides across level, nearly frictionless ice at constant velocity. What is the net horizontal force on the puck? Explain why the puck can keep moving even though the net force is zero.',
    givens:['The puck moves in a straight line.','Its velocity is constant.','Horizontal friction is negligible.'],
    expectedReasoning:['Identify constant velocity as zero acceleration.','Use F_net = ma.','Conclude that net force is zero.','Distinguish maintaining velocity from causing acceleration.'],
    checkpoints:[{id:'velocity',label:'Velocity',expected:'Constant velocity means acceleration is zero.'},{id:'net-force',label:'Net force',expected:'Zero acceleration implies zero net force.'},{id:'causation',label:'Causal model',expected:'Net force changes velocity; it is not required to sustain constant velocity.'}],
    answer:'The net horizontal force is 0 N because constant velocity means zero acceleration. Motion does not require a continuing net force.' },
  { id:'force-motion-transfer-1', misconceptionCode:'force_causes_motion', conceptId:'forces', prerequisiteConceptId:'motion', stage:'transfer',
    prompt:'A 2 kg cart moves east at 3 m/s. A horizontal net force of 4 N east acts on it for 2 s. Find its acceleration and final velocity. Explain what the force changes.',
    givens:['m = 2 kg','initial velocity = 3 m/s east','net force = 4 N east','time = 2 s'],
    expectedReasoning:['Apply F_net = ma.','Calculate a = 2 m/s² east.','Use v = u + at.','Calculate final velocity = 7 m/s east.','State that the force changes velocity by producing acceleration.'],
    checkpoints:[{id:'equation',label:'Force equation',expected:'Use net force to determine acceleration.'},{id:'units',label:'Units',expected:'Acceleration is m/s² and velocity is m/s.'},{id:'change',label:'Change in motion',expected:'The force changes velocity through acceleration.'}],
    answer:'a = 4/2 = 2 m/s² east; v = 3 + (2)(2) = 7 m/s east.' },
  { id:'heat-temperature-discrimination-1', misconceptionCode:'heat_equals_temperature', conceptId:'temperature_heat', prerequisiteConceptId:'energy', stage:'discrimination',
    prompt:'Two identical cups contain equal masses of water. Cup A is at 20 °C and Cup B is at 60 °C. Is temperature itself a quantity of heat contained in the water? Explain what temperature and heat mean here.',
    givens:['Equal water masses.','Cup A: 20 °C.','Cup B: 60 °C.'],
    expectedReasoning:['Describe temperature as a measure related to microscopic energy distribution.','Describe heat as energy transferred because of a temperature difference.','Do not treat temperature as an amount of heat.'],
    checkpoints:[{id:'temperature',label:'Temperature',expected:'Temperature characterizes the thermal state of matter.'},{id:'heat',label:'Heat',expected:'Heat is energy transferred due to a temperature difference.'}],
    answer:'No. Temperature is not an amount of heat. Heat refers to energy transferred because of a temperature difference.' },
  { id:'energy-force-discrimination-1', misconceptionCode:'energy_as_force', conceptId:'energy', prerequisiteConceptId:'forces', stage:'discrimination',
    prompt:'A 5 N horizontal force pushes a box 4 m in the direction of the force. Calculate the work done and explain why work and force are not the same physical quantity.',
    givens:['F = 5 N','displacement = 4 m','force and displacement are parallel.'],
    expectedReasoning:['Identify force as an interaction.','Use W = Fd for parallel force and displacement.','Calculate W = 20 J.','Distinguish force in newtons from work/energy in joules.'],
    checkpoints:[{id:'interaction',label:'Force',expected:'Force describes an interaction and has units of newtons.'},{id:'work',label:'Work',expected:'Work is energy transferred by a force through displacement.'},{id:'units',label:'Units',expected:'Force is N; work and energy are J.'}],
    answer:'W = Fd = 5 × 4 = 20 J. Force and work are different quantities with different meanings and units.' },
  { id:'direction-scalar-discrimination-1', misconceptionCode:'direction_as_scalar', conceptId:'forces', prerequisiteConceptId:'vectors', stage:'discrimination',
    prompt:'A 10 N force acts east while a 6 N force acts west on the same object. Find the net force and state its direction. Explain why simply adding 10 + 6 is not sufficient.',
    givens:['10 N east','6 N west'],
    expectedReasoning:['Choose a positive direction.','Represent west as negative relative to east.','Compute 10 - 6 = 4 N.','State the direction is east.'],
    checkpoints:[{id:'direction',label:'Direction',expected:'Opposite directions require signed/vector treatment.'},{id:'result',label:'Net force',expected:'The net force is 4 N east.'}],
    answer:'The net force is 4 N east. Opposing vectors cannot be combined as unsigned scalars.' },
  { id:'ratio-additive-discrimination-1', misconceptionCode:'ratio_additive', conceptId:'fractions', prerequisiteConceptId:'arithmetic', stage:'discrimination',
    prompt:'A recipe uses flour and sugar in a 3:2 ratio. If the recipe is doubled, how much flour is needed when the original recipe used 6 cups? Explain why doubling preserves the ratio.',
    givens:['Flour:sugar = 3:2','Original flour = 6 cups','Scale factor = 2'],
    expectedReasoning:['Recognize 6 cups is twice the ratio unit of 3.','Use multiplicative scaling.','Double 6 cups to obtain 12 cups.','State that both quantities scale by the same factor.'],
    checkpoints:[{id:'scale',label:'Scale factor',expected:'Doubling means multiplying by 2.'},{id:'relationship',label:'Ratio relationship',expected:'A ratio expresses a multiplicative relationship.'}],
    answer:'12 cups. The ratio is preserved by multiplying both quantities by the same scale factor.' },
];

const PLANS: Readonly<Record<string, InterventionPlan>> = {
  force_causes_motion:{misconceptionCode:'force_causes_motion',prerequisiteConceptId:'motion',strategy:'Contrast constant-velocity motion with acceleration, then require transfer to a numerical Newton’s-law problem.',problems:PROBLEMS.filter(p=>p.misconceptionCode==='force_causes_motion')},
  heat_equals_temperature:{misconceptionCode:'heat_equals_temperature',prerequisiteConceptId:'energy',strategy:'Separate thermal state from energy transfer, then test the distinction in a new thermal context.',problems:PROBLEMS.filter(p=>p.misconceptionCode==='heat_equals_temperature')},
  energy_as_force:{misconceptionCode:'energy_as_force',prerequisiteConceptId:'forces',strategy:'Contrast interaction (force) with transferred energy (work), including units and equations.',problems:PROBLEMS.filter(p=>p.misconceptionCode==='energy_as_force')},
  direction_as_scalar:{misconceptionCode:'direction_as_scalar',prerequisiteConceptId:'vectors',strategy:'Make direction operational through signed components before returning to physical vector combinations.',problems:PROBLEMS.filter(p=>p.misconceptionCode==='direction_as_scalar')},
  ratio_additive:{misconceptionCode:'ratio_additive',prerequisiteConceptId:'arithmetic',strategy:'Repair the multiplicative meaning of ratios using scale factors before returning to proportional physics problems.',problems:PROBLEMS.filter(p=>p.misconceptionCode==='ratio_additive')},
};

export function getInterventionPlan(finding:Pick<DiagnosticFinding,'code'>):InterventionPlan|undefined { return PLANS[finding.code]; }
export function getRemediationProblem(problemId:string):RemediationProblem { const p=PROBLEMS.find(x=>x.id===problemId); if(!p) throw new Error(`Unknown remediation problem: ${problemId}`); return p; }
export function getAllRemediationProblems():readonly RemediationProblem[] { return PROBLEMS; }
