import { diagnoseReasoning } from './diagnostics.js';
import { evaluateCriterion } from './problem-answer-spec.js';
import type { PracticeProblem } from './practice.js';

export type PracticeVerdict='correct'|'incorrect'|'insufficient_evidence'|'misconception_detected';
export interface PracticeEvaluation { verdict:PracticeVerdict; correct:boolean; checkpointScore:number; matchedCheckpoints:string[]; missingCheckpoints:string[]; misconceptions:string[]; }

export function evaluatePractice(problem:PracticeProblem,reasoning:string,answer:string):PracticeEvaluation{
  const text=`${reasoning}\n${answer}`.trim();
  if(!text)return{verdict:'insufficient_evidence',correct:false,checkpointScore:0,matchedCheckpoints:[],missingCheckpoints:problem.checkpoints.map(c=>c.id),misconceptions:[]};
  const matched=problem.checkpoints.filter(c=>c.patterns.some(pattern=>pattern.test(text))).map(c=>c.id);
  const missing=problem.checkpoints.filter(c=>!matched.includes(c.id)).map(c=>c.id);
  const score=problem.checkpoints.length?matched.length/problem.checkpoints.length:0;
  const answerMatched=problem.answerSpec.criteria.every(c=>evaluateCriterion(c,c.kind==='numeric'?answer:text));
  const misconceptions=diagnoseReasoning(problem.conceptId,reasoning).map(f=>f.code);
  if(misconceptions.length)return{verdict:'misconception_detected',correct:false,checkpointScore:score,matchedCheckpoints:matched,missingCheckpoints:missing,misconceptions};
  if(answerMatched&&score===1)return{verdict:'correct',correct:true,checkpointScore:score,matchedCheckpoints:matched,missingCheckpoints:[],misconceptions:[]};
  if(answerMatched||score>0)return{verdict:'insufficient_evidence',correct:false,checkpointScore:score,matchedCheckpoints:matched,missingCheckpoints:missing,misconceptions:[]};
  return{verdict:'incorrect',correct:false,checkpointScore:score,matchedCheckpoints:matched,missingCheckpoints:missing,misconceptions:[]};
}
