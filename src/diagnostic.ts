import { CURRICULUM, Concept, getConcept, missingRequirements } from './curriculum.js';
import type { LearningRepository } from './learning-repository.js';

export type EvidenceKind='diagnostic'|'problem'|'explanation'|'transfer'|'placement'|'attempt';
export interface DiagnosticObservation { conceptId:string;score:number;kind:EvidenceKind;difficulty:number;note?:string; }
export interface DiagnosticResult { scores:Record<string,number>;confidence:Record<string,number>;recommendedConcept:string|null;unresolvedPrerequisites:string[]; }

const weightFor=(kind:EvidenceKind,difficulty:number):number=>{const kindWeight:Record<EvidenceKind,number>={diagnostic:1,problem:1,explanation:1.15,transfer:1.35,placement:0.8,attempt:1};return kindWeight[kind]*Math.max(0.5,Math.min(1.5,difficulty));};

export function diagnosticCandidates(mastery:Record<string,number>,limit=6):Concept[]{const physics=CURRICULUM.filter(c=>c.domain!=='mathematics'&&c.domain!=='engineering');const domains=['mechanics','thermal_physics','waves_optics','electricity_magnetism','modern_physics'];const ranked=[...domains.flatMap(domain=>physics.filter(c=>c.domain===domain).filter(c=>(mastery[c.id]??0)<100).slice(0,2)),...physics.filter(c=>(mastery[c.id]??0)<100)];return [...new Map(ranked.map(c=>[c.id,c])).values()].slice(0,limit);}

export class DiagnosticEngine{
  constructor(private readonly store:LearningRepository){}
  evaluate(studentId:number,observations:DiagnosticObservation[]):DiagnosticResult{return this.store.transaction(()=>{
    for(const observation of observations){getConcept(observation.conceptId);if(!Number.isFinite(observation.score)||observation.score<0||observation.score>100)throw new Error('Diagnostic score must be between 0 and 100');if(!Number.isFinite(observation.difficulty)||observation.difficulty<=0)throw new Error('Diagnostic difficulty must be positive');this.store.addEvidence(studentId,observation.conceptId,observation.kind,observation.score,JSON.stringify({difficulty:observation.difficulty,note:observation.note??'Diagnostic evidence'}));}
    const scores:Record<string,number>={};const confidence:Record<string,number>={};
    const grouped=new Map<string,Array<{score:number;kind:string;difficulty:number}>>();
    for(const evidence of this.store.listEvidence(studentId)){if(evidence.value===null)continue;const list=grouped.get(evidence.conceptId)??[];let difficulty=1;try{const parsed=JSON.parse(evidence.note);if(Number.isFinite(parsed.difficulty)&&parsed.difficulty>0)difficulty=parsed.difficulty;}catch{}list.push({score:evidence.value,kind:evidence.kind,difficulty});grouped.set(evidence.conceptId,list);}
    for(const[conceptId,list]of grouped){const weighted=list.reduce((sum,o)=>sum+o.score*weightFor(o.kind as EvidenceKind,o.difficulty),0);const totalWeight=list.reduce((sum,o)=>sum+weightFor(o.kind as EvidenceKind,o.difficulty),0);scores[conceptId]=Math.round((weighted/totalWeight)*10)/10;confidence[conceptId]=Math.round(Math.min(1,totalWeight/5)*100)/100;this.store.setMastery(studentId,conceptId,scores[conceptId]);}
    const mastery=this.store.getMastery(studentId);const recommended=CURRICULUM.find(c=>c.domain!=='mathematics'&&c.domain!=='engineering'&&(mastery[c.id]??0)<70&&missingRequirements(mastery,c.id).length===0)??null;return{scores,confidence,recommendedConcept:recommended?.id??null,unresolvedPrerequisites:recommended?missingRequirements(mastery,recommended.id):[]};
  });}
}
