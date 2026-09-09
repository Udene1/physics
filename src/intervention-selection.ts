import type { InterventionRecord, MisconceptionRecord } from './store.js';

export interface InterventionSelection { interventionId:number; misconceptionCode:string; reason:string; priority:number; }

/** Select the smallest repair that is both blocking and sufficiently evidenced. */
export function selectIntervention(
  misconceptions:readonly MisconceptionRecord[],
  interventions:readonly InterventionRecord[],
):InterventionSelection|undefined {
  const active=interventions.filter(i=>i.status==='queued'||i.status==='active');
  const ranked=active.map(i=>{
    const m=misconceptions.find(x=>x.id===i.misconceptionId);
    if(!m)return undefined;
    const evidence=m.occurrences;
    const severity=m.severity;
    // Higher severity and repeated evidence win; prerequisite repairs remain targeted by the stored plan.
    const priority=severity*100+Math.min(evidence,10)*10+(i.stage==='discrimination'?5:0);
    return {interventionId:i.id,misconceptionCode:m.code,priority,reason:evidence>1?'Repeated evidence indicates this pattern is persistent.':'This is the earliest targeted repair for the active misconception.'};
  }).filter((x):x is InterventionSelection=>Boolean(x));
  return ranked.sort((a,b)=>b.priority-a.priority||a.interventionId-b.interventionId)[0];
}

export function learnerFacingIntervention(misconception:MisconceptionRecord,selection:InterventionSelection):{blocking:string;noticed:string;why:string} {
  return {
    blocking:`This pattern is currently blocking progress in ${misconception.conceptId}.`,
    noticed:`Vita noticed this pattern ${misconception.occurrences} time${misconception.occurrences===1?'':'s'} in your work.`,
    why:`We are repairing the underlying idea first rather than restarting the whole lesson.`,
  };
}
