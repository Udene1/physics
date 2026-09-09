import { diagnoseReasoning } from './diagnostics.js';
import type { RemediationProblem, RemediationVerdict } from './interventions.js';

export interface RemediationEvaluation { verdict:RemediationVerdict; checkpointScore:number; matchedCheckpoints:string[]; missingCheckpoints:string[]; newMisconceptions:string[]; }

const CHECKPOINT_PATTERNS:Record<string,RegExp[]> = {
  velocity:[/constant velocity/i,/velocity.*constant/i,/acceleration.*zero/i,/acceleration.*0/i],
  'net-force':[/net force.*zero/i,/net force.*0/i,/force.*zero/i,/force.*0/i],
  causation:[/force.*acceleration/i,/acceleration.*change.*velocity/i,/not.*(require|need).*force.*(motion|move)/i,/motion.*not.*require.*force/i],
  equation:[/f\s*[_ ]?net\s*=\s*m\s*a/i,/f\s*=\s*m\s*a/i,/force.*mass.*acceleration/i],
  units:[/m\/s\^?2/i,/m\/s²/i,/m\/s/i,/newton|\bn\b/i,/joule|\bj\b/i],
  change:[/force.*change.*velocity/i,/force.*acceleration/i,/acceleration.*velocity/i],
  temperature:[/temperature.*thermal/i,/temperature.*microscopic/i,/temperature.*distribution/i],
  heat:[/heat.*transfer/i,/energy.*transfer.*temperature/i,/temperature difference.*transfer/i],
  interaction:[/force.*interaction/i],
  work:[/work.*energy.*transfer/i,/work.*force.*displacement/i],
  direction:[/opposite.*direction/i,/direction.*(signed|vector)/i,/west.*negative/i,/east.*positive/i],
  result:[/4\s*n.*east/i,/4\s*newton.*east/i,/net force.*4/i],
  scale:[/multiply.*2/i,/doubl/i,/scale factor.*2/i],
  relationship:[/ratio.*multiplicative/i,/multiplicative.*ratio/i,/same.*scale factor/i],
};

function checkpointMatched(id:string,text:string):boolean { return (CHECKPOINT_PATTERNS[id]??[]).some(p=>p.test(text)); }

export function evaluateRemediation(problem:RemediationProblem, reasoning:string, answer:string, correct:boolean):RemediationEvaluation {
  const text=`${reasoning}\n${answer}`.trim();
  if(!text) return {verdict:'insufficient_evidence',checkpointScore:0,matchedCheckpoints:[],missingCheckpoints:problem.checkpoints.map(c=>c.id),newMisconceptions:[]};
  const matched=problem.checkpoints.filter(c=>checkpointMatched(c.id,text)).map(c=>c.id);
  const missing=problem.checkpoints.filter(c=>!matched.includes(c.id)).map(c=>c.id);
  const score=problem.checkpoints.length===0?0:matched.length/problem.checkpoints.length;
  const findings=diagnoseReasoning(problem.conceptId,reasoning);
  const newMisconceptions=findings.filter(f=>f.code!==problem.misconceptionCode).map(f=>f.code);
  const sameMisconception=findings.some(f=>f.code===problem.misconceptionCode);
  if(newMisconceptions.length) return {verdict:'new_misconception',checkpointScore:score,matchedCheckpoints:matched,missingCheckpoints:missing,newMisconceptions};
  if(sameMisconception) return {verdict:'still_present',checkpointScore:score,matchedCheckpoints:matched,missingCheckpoints:missing,newMisconceptions:[]};
  if(correct && score===1) return {verdict:'repaired',checkpointScore:score,matchedCheckpoints:matched,missingCheckpoints:[],newMisconceptions:[]};
  return {verdict:'insufficient_evidence',checkpointScore:score,matchedCheckpoints:matched,missingCheckpoints:missing,newMisconceptions:[]};
}
