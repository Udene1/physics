import test from 'node:test';
import assert from 'node:assert/strict';
import { selectIntervention, learnerFacingIntervention } from '../src/intervention-selection.js';
import type { InterventionRecord, MisconceptionRecord } from '../src/store.js';

const misconception=(id:number,code:string,severity:number,occurrences:number):MisconceptionRecord=>({id,studentId:1,conceptId:'forces',code,severity,status:'active',occurrences,lastEvidenceId:null,updatedAt:new Date().toISOString()});
const intervention=(id:number,misconceptionId:number,stage:'discrimination'|'transfer'):InterventionRecord=>({id,studentId:1,misconceptionId,conceptId:'forces',prerequisiteConceptId:'motion',problemId:`p-${id}`,stage,status:'queued',strategy:'repair',createdAt:new Date().toISOString(),updatedAt:new Date().toISOString()});

test('selection prioritizes severity and repeated evidence',()=>{
 const m=[misconception(1,'minor',1,1),misconception(2,'persistent',3,3)];
 const i=[intervention(1,1,'discrimination'),intervention(2,2,'discrimination')];
 const selected=selectIntervention(m,i)!;
 assert.equal(selected.interventionId,2);
 assert.match(selected.reason,/Repeated evidence/);
});

test('learner-facing state explains the repair without exposing internal diagnosis mechanics',()=>{
 const m=misconception(2,'force_causes_motion',3,2);
 const i=intervention(2,2,'discrimination');
 const selected=selectIntervention([m],[i])!;
 const message=learnerFacingIntervention(m,selected);
 assert.match(message.blocking,/blocking/);
 assert.match(message.noticed,/2 times/);
 assert.match(message.why,/underlying idea/);
});
