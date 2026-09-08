export type ProblemAnswerType = 'numeric' | 'choice' | 'short_text';
export interface ReasoningCriterion { id:string; keywords:string[]; }

export interface PhysicsProblem {
  id:string;
  conceptId:string;
  title:string;
  prompt:string;
  difficulty:number;
  answerType:ProblemAnswerType;
  answer:string;
  tolerance?:number;
  choices?:string[];
  reasoningPrompts:string[];
  reasoningCriteria:ReasoningCriterion[];
}

export const PHYSICS_PROBLEMS: readonly PhysicsProblem[] = [
  { id:'measurement-length-unit', conceptId:'measurement', title:'Measure before calculating', prompt:'A table is measured as 1.20 m long. Express its length in centimetres.', difficulty:1, answerType:'numeric', answer:'120', tolerance:0, reasoningPrompts:['What quantity are you converting?','What relationship between metres and centimetres did you use?'], reasoningCriteria:[{id:'quantity-identification',keywords:['length','table','1.20 m','metres']},{id:'unit-conversion',keywords:['100 centimetres','100 cm','1 m = 100','multiply by 100','times 100']},{id:'unit',keywords:['cm','centimetres','centimeter']}] },
  { id:'motion-average-speed', conceptId:'motion', title:'Average speed from a journey', prompt:'A cyclist travels 150 m in 30 s. What is the cyclist’s average speed?', difficulty:1, answerType:'numeric', answer:'5', tolerance:0, reasoningPrompts:['What measured quantities matter?','What equation connects distance, time, and average speed?','Why is this an average rather than an instantaneous speed?'], reasoningCriteria:[{id:'quantities',keywords:['distance','150 m','time','30 s']},{id:'speed-model',keywords:['speed = distance / time','distance / time','distance divided by time','v = d/t','d/t']},{id:'average',keywords:['average','whole journey','total distance','total time']},{id:'units',keywords:['m/s','metres per second']}] },
  { id:'motion-position-change', conceptId:'motion', title:'Position is not distance', prompt:'A student walks 10 m east and then 10 m west back to the starting point. What is the student’s displacement?', difficulty:2, answerType:'numeric', answer:'0', tolerance:0, reasoningPrompts:['What is the final position relative to the initial position?','Why is displacement different from total distance travelled?'], reasoningCriteria:[{id:'initial-final-position',keywords:['starting point','initial position','final position','back to']},{id:'direction',keywords:['east','west','opposite direction','opposite']},{id:'displacement-model',keywords:['displacement','final minus initial','change in position','zero displacement']},{id:'distance-distinction',keywords:['distance','20 m','total distance']}] },
  { id:'forces-net-force', conceptId:'forces', title:'Net force predicts acceleration', prompt:'A 2 kg object experiences a net force of 10 N to the right. What is its acceleration?', difficulty:2, answerType:'numeric', answer:'5', tolerance:0, reasoningPrompts:['What physical law connects net force, mass, and acceleration?','What direction should the acceleration have?'], reasoningCriteria:[{id:'newtons-second-law',keywords:["Newton's second law",'F = ma','f=ma','force = mass x acceleration','force equals mass times acceleration']},{id:'quantities',keywords:['force','10 N','mass','2 kg']},{id:'direction',keywords:['right','to the right','same direction']},{id:'units',keywords:['m/s²','m/s2','metres per second squared']}] },
];

const byId = new Map(PHYSICS_PROBLEMS.map(problem => [problem.id, problem]));
export function getProblem(id:string):PhysicsProblem { const problem=byId.get(id); if(!problem) throw new Error(`Unknown problem: ${id}`); return problem; }
export function problemsForConcept(conceptId:string):PhysicsProblem[] { return PHYSICS_PROBLEMS.filter(problem=>problem.conceptId===conceptId); }
export function isAnswerCorrect(problem:PhysicsProblem, answer:string):boolean { if(problem.answerType==='numeric'){const actual=Number(answer.trim());const expected=Number(problem.answer);return Number.isFinite(actual)&&Math.abs(actual-expected)<=(problem.tolerance??0);} return answer.trim().toLowerCase()===problem.answer.trim().toLowerCase(); }
