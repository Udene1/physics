import { getConcept } from './curriculum.js';

export interface LessonStep { id:string; type:'observe'|'model'|'math'|'predict'|'test'|'explain'; prompt:string; expectedEvidence:string[]; }
export interface PhysicsLesson { id:string; conceptId:string; title:string; goal:string; difficulty:number; steps:LessonStep[]; }

export const PHYSICS_LESSONS: readonly PhysicsLesson[] = [
  { id:'motion-from-change', conceptId:'motion', title:'Motion is change', goal:'Build motion models from position and time before introducing formulas.', difficulty:1, steps:[
    {id:'observe',type:'observe',prompt:'Describe what changes when an object moves and what could be measured.',expectedEvidence:['position','time']},
    {id:'model',type:'model',prompt:'Explain how two measurements can describe how quickly position changes.',expectedEvidence:['change','position','time']},
    {id:'math',type:'math',prompt:'Write a relationship for average speed using distance and elapsed time.',expectedEvidence:['distance','time','divide']},
    {id:'predict',type:'predict',prompt:'Predict the speed of an object travelling 20 m in 4 s.',expectedEvidence:['5']},
    {id:'test',type:'test',prompt:'Compare your prediction with the measured journey and explain any difference.',expectedEvidence:['measurement','prediction']},
    {id:'explain',type:'explain',prompt:'Explain why average speed describes a whole journey rather than one instant.',expectedEvidence:['average','journey']},
  ]},
  { id:'forces-as-interactions', conceptId:'forces', title:'Forces change motion', goal:'Use interaction models and net force to predict acceleration.', difficulty:2, steps:[
    {id:'observe',type:'observe',prompt:'Identify the interactions acting on a moving object.',expectedEvidence:['force','interaction']},
    {id:'model',type:'model',prompt:'Explain why opposing forces combine into a net force.',expectedEvidence:['net','opposite']},
    {id:'math',type:'math',prompt:'Relate net force, mass and acceleration with an equation.',expectedEvidence:['F = ma','force','mass','acceleration']},
    {id:'predict',type:'predict',prompt:'Predict the acceleration when 10 N acts on a 2 kg object.',expectedEvidence:['5','m/s']},
    {id:'test',type:'test',prompt:'Check whether the predicted acceleration points with or against the net force.',expectedEvidence:['direction','net force']},
    {id:'explain',type:'explain',prompt:'Explain what would change if the mass doubled while net force stayed fixed.',expectedEvidence:['mass','acceleration']},
  ]},
  { id:'energy-transfer', conceptId:'energy', title:'Energy moves between systems', goal:'Treat work and energy as a physical accounting model.', difficulty:2, steps:[
    {id:'observe',type:'observe',prompt:'Describe an everyday event where a force changes an object’s motion.',expectedEvidence:['force','motion']},
    {id:'model',type:'model',prompt:'Explain work as energy transferred by a force through displacement.',expectedEvidence:['work','energy','displacement']},
    {id:'math',type:'math',prompt:'Use W = Fd for a force aligned with displacement.',expectedEvidence:['W = Fd','force','distance']},
    {id:'predict',type:'predict',prompt:'Predict the work done by 20 N over 3 m.',expectedEvidence:['60','joules']},
    {id:'test',type:'test',prompt:'Identify what measurement would reveal whether the prediction is reasonable.',expectedEvidence:['force','distance','measurement']},
    {id:'explain',type:'explain',prompt:'Explain where the transferred energy goes in a real system with friction.',expectedEvidence:['friction','thermal','energy']},
  ]},
  { id:'waves-as-relationships', conceptId:'waves', title:'Waves carry patterns', goal:'Connect frequency, wavelength and propagation speed.', difficulty:2, steps:[
    {id:'observe',type:'observe',prompt:'Describe a repeating disturbance and identify what repeats.',expectedEvidence:['repeat','pattern']},
    {id:'model',type:'model',prompt:'Explain wavelength and frequency as measurable properties of a wave.',expectedEvidence:['wavelength','frequency']},
    {id:'math',type:'math',prompt:'Write the relationship between wave speed, frequency and wavelength.',expectedEvidence:['v = fλ','frequency','wavelength']},
    {id:'predict',type:'predict',prompt:'Predict wave speed for 4 Hz and 2 m wavelength.',expectedEvidence:['8','m/s']},
    {id:'test',type:'test',prompt:'Describe a measurement that could test the predicted speed.',expectedEvidence:['distance','time','measure']},
    {id:'explain',type:'explain',prompt:'Explain why the medium can affect wave speed without changing the basic relationship.',expectedEvidence:['medium','speed','frequency']},
  ]},
  { id:'circuits-as-systems', conceptId:'circuits', title:'Circuits are physical systems', goal:'Model voltage, current and power in a safe low-voltage circuit.', difficulty:2, steps:[
    {id:'observe',type:'observe',prompt:'Identify what must be connected for a low-voltage circuit to operate.',expectedEvidence:['circuit','closed','connection']},
    {id:'model',type:'model',prompt:'Distinguish voltage as energy per charge from current as charge flow rate.',expectedEvidence:['voltage','energy','charge','current']},
    {id:'math',type:'math',prompt:'Relate voltage and current to electrical power.',expectedEvidence:['P = VI','voltage','current']},
    {id:'predict',type:'predict',prompt:'Predict power at 6 V and 2 A.',expectedEvidence:['12','watts']},
    {id:'test',type:'test',prompt:'Plan a safe low-voltage measurement of voltage and current.',expectedEvidence:['measure','voltage','current']},
    {id:'explain',type:'explain',prompt:'Explain why electrical power is an energy-transfer rate.',expectedEvidence:['energy','time','rate']},
  ]},
  { id:'modern-physics-branch', conceptId:'relativity', title:'When classical intuition breaks', goal:'Recognize when relativity and quantum theory require new physical models.', difficulty:3, steps:[
    {id:'observe',type:'observe',prompt:'Describe a physical prediction that classical mechanics struggles to explain.',expectedEvidence:['classical','prediction']},
    {id:'model',type:'model',prompt:'Explain why invariant light speed changes the model of space and time.',expectedEvidence:['light','invariant','space','time']},
    {id:'math',type:'math',prompt:'Identify the role of relationships and reference frames without assuming absolute time.',expectedEvidence:['reference frame','relative','time']},
    {id:'predict',type:'predict',prompt:'Predict qualitatively what happens to elapsed time for a clock moving close to light speed.',expectedEvidence:['time dilation','slower','relative']},
    {id:'test',type:'test',prompt:'Describe what observation could distinguish classical absolute-time reasoning from relativity.',expectedEvidence:['measurement','clock','motion']},
    {id:'explain',type:'explain',prompt:'Explain one reason a learner might choose relativity as a Modern Physics specialization.',expectedEvidence:['relativity','specialization']},
  ]},
];

const byId=new Map(PHYSICS_LESSONS.map(lesson=>[lesson.id,lesson]));
export function getLesson(id:string):PhysicsLesson{const lesson=byId.get(id);if(!lesson)throw new Error(`Unknown lesson: ${id}`);getConcept(lesson.conceptId);return lesson;}
export function lessonsForConcept(conceptId:string):PhysicsLesson[]{getConcept(conceptId);return PHYSICS_LESSONS.filter(lesson=>lesson.conceptId===conceptId);}
