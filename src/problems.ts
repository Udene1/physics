export type ProblemAnswerType = 'numeric' | 'choice' | 'short_text';

export interface ReasoningCriterion {
  id: string;
  description: string;
  keywords: string[];
  required?: boolean;
  misconceptionCode?: string;
}

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
  reasoningCriteria: ReasoningCriterion[];
}

export const PHYSICS_PROBLEMS: readonly PhysicsProblem[] = [
  { id:'measurement-length-unit', conceptId:'measurement', title:'Measure before calculating', prompt:'A table is measured as 1.20 m long. Express its length in centimetres.', difficulty:1, answerType:'numeric', answer:'120', tolerance:0, reasoningPrompts:['What quantity are you converting?','What relationship between metres and centimetres did you use?'], reasoningCriteria:[
    {id:'quantity-identification',description:'Identifies the measured length and its starting unit.',keywords:['length','table','1.20 m','metres'],required:true,misconceptionCode:'measurement-missing-quantity'},
    {id:'unit-conversion',description:'Uses the metre-to-centimetre conversion correctly.',keywords:['100 centimetres','100 cm','1 m = 100','multiply by 100','times 100'],required:true,misconceptionCode:'measurement-wrong-conversion'},
    {id:'unit',description:'States the resulting unit as centimetres.',keywords:['cm','centimetres','centimeter'],required:true,misconceptionCode:'measurement-missing-unit'}
  ] },
  { id:'motion-average-speed', conceptId:'motion', title:'Average speed from a journey', prompt:'A cyclist travels 150 m in 30 s. What is the cyclist’s average speed?', difficulty:1, answerType:'numeric', answer:'5', tolerance:0, reasoningPrompts:['What measured quantities matter?','What equation connects distance, time, and average speed?','Why is this an average rather than an instantaneous speed?'], reasoningCriteria:[
    {id:'quantities',description:'Identifies distance and elapsed time as the relevant quantities.',keywords:['distance','150 m','time','30 s'],required:true,misconceptionCode:'speed-missing-quantities'},
    {id:'speed-model',description:'Selects the model average speed = distance / time.',keywords:['speed = distance / time','distance / time','distance divided by time','v = d/t','d/t'],required:true,misconceptionCode:'speed-wrong-model'},
    {id:'average',description:'Recognizes that the calculation describes the whole journey.',keywords:['average','whole journey','total distance','total time'],required:true,misconceptionCode:'speed-missing-average-concept'},
    {id:'units',description:'Tracks the resulting speed unit as metres per second.',keywords:['m/s','metres per second'],required:true,misconceptionCode:'speed-wrong-unit'}
  ] },
  { id:'motion-position-change', conceptId:'motion', title:'Position is not distance', prompt:'A student walks 10 m east and then 10 m west back to the starting point. What is the student’s displacement?', difficulty:2, answerType:'numeric', answer:'0', tolerance:0, reasoningPrompts:['What is the final position relative to the initial position?','Why is displacement different from total distance travelled?'], reasoningCriteria:[
    {id:'initial-final-position',description:'Compares final position with initial position.',keywords:['starting point','initial position','final position','back to'],required:true,misconceptionCode:'displacement-missing-position'},
    {id:'direction',description:'Tracks the opposing directions of the two movements.',keywords:['east','west','opposite direction','opposite'],required:true,misconceptionCode:'displacement-missing-direction'},
    {id:'displacement-model',description:'Treats displacement as change in position.',keywords:['displacement','final minus initial','change in position','zero displacement'],required:true,misconceptionCode:'displacement-wrong-model'},
    {id:'distance-distinction',description:'Distinguishes displacement from total distance travelled.',keywords:['distance','20 m','total distance'],required:true,misconceptionCode:'displacement-confuses-distance'}
  ] },
  { id:'forces-net-force', conceptId:'forces', title:'Net force predicts acceleration', prompt:'A 2 kg object experiences a net force of 10 N to the right. What is its acceleration?', difficulty:2, answerType:'numeric', answer:'5', tolerance:0, reasoningPrompts:['What physical law connects net force, mass, and acceleration?','What direction should the acceleration have?'], reasoningCriteria:[
    {id:'newtons-second-law',description:'Uses Newton’s second law to connect force, mass and acceleration.',keywords:["Newton's second law",'F = ma','f=ma','force = mass x acceleration','force equals mass times acceleration'],required:true,misconceptionCode:'forces-wrong-model'},
    {id:'quantities',description:'Identifies net force and mass.',keywords:['force','10 N','mass','2 kg'],required:true,misconceptionCode:'forces-missing-quantities'},
    {id:'direction',description:'Infers acceleration in the direction of the net force.',keywords:['right','to the right','same direction'],required:true,misconceptionCode:'forces-wrong-direction'},
    {id:'units',description:'Reports acceleration in metres per second squared.',keywords:['m/s²','m/s2','metres per second squared'],required:true,misconceptionCode:'forces-wrong-unit'}
  ] },
  { id:'graphs-slope-speed', conceptId:'graphs', title:'Read motion from a graph', prompt:'A position-time graph shows position increasing from 0 m to 20 m over 4 s. What speed does the slope represent?', difficulty:2, answerType:'numeric', answer:'5', tolerance:0, reasoningPrompts:['What two quantities determine the slope?','What physical quantity does position change per unit time represent?'], reasoningCriteria:[
    {id:'slope-model',description:'Uses slope as change in vertical quantity divided by change in horizontal quantity.',keywords:['slope','change in position / time','change in position divided by time','rise over run','20 m / 4 s'],required:true,misconceptionCode:'graphs-wrong-slope-model'},
    {id:'physical-meaning',description:'Connects position change per time to speed.',keywords:['speed','velocity','position per time'],required:true,misconceptionCode:'graphs-missing-physical-meaning'},
    {id:'units',description:'Tracks metres per second for the slope.',keywords:['m/s','metres per second'],required:true,misconceptionCode:'graphs-wrong-unit'}
  ] },
];

const byId = new Map(PHYSICS_PROBLEMS.map(problem => [problem.id, problem]));
export function getProblem(id:string):PhysicsProblem { const problem=byId.get(id);if(!problem)throw new Error(`Unknown problem: ${id}`);return problem; }
export function problemsForConcept(conceptId:string):PhysicsProblem[] { return PHYSICS_PROBLEMS.filter(problem=>problem.conceptId===conceptId); }
export function isAnswerCorrect(problem:PhysicsProblem,answer:string):boolean { if(problem.answerType==='numeric'){const actual=Number(answer.trim());const expected=Number(problem.answer);return Number.isFinite(actual)&&Math.abs(actual-expected)<=(problem.tolerance??0);}return answer.trim().toLowerCase()===problem.answer.trim().toLowerCase(); }
