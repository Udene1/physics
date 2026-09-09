import { getConcept } from './curriculum.js';

export interface DiagnosticFinding { code:string; severity:number; evidence:string; remediation:string; }
interface Rule { code:string; severity:number; patterns:RegExp[]; remediation:string; }

const RULES:readonly Rule[]=[
  {code:'ratio_additive',severity:3,patterns:[/ratio.{0,30}(add|plus|subtract|minus)/i,/treat(?:ed|ing).{0,20}ratio.{0,20}(add|subtract)/i],remediation:'Repair proportional reasoning: represent a ratio as a multiplicative relationship before calculating.'},
  {code:'direction_as_scalar',severity:3,patterns:[/ignore.{0,20}(direction|sign)/i,/direction.{0,20}(doesn.?t|does not|not).{0,20}matter/i,/just add.{0,20}(velocity|force|vector)/i],remediation:'Repair vector reasoning: separate magnitude from direction and resolve components before combining vectors.'},
  {code:'force_causes_motion',severity:4,patterns:[/force.{0,30}(causes|creates|produces).{0,30}(motion|velocity)/i,/no\s+force.{0,50}(means|mean|so).{0,50}(no\s+motion|stopped|cannot\s+keep\s+moving|cannot\s+move)/i,/moving.{0,30}(means|must|needs|requires|need).{0,30}force/i,/moving.{0,30}(need|requires).{0,30}force/i],remediation:'Repair Newtonian reasoning: distinguish velocity from acceleration and ask whether net force is zero or nonzero.'},
  {code:'energy_as_force',severity:3,patterns:[/energy.{0,20}(is|means|equals).{0,20}force/i,/use.{0,10}energy.{0,20}(instead of|as).{0,20}force/i,/work.{0,30}(and|&).{0,30}force.{0,30}(same|equal)/i,/force.{0,30}(is|equals).{0,30}(work|energy)/i],remediation:'Repair model selection: energy tracks capacity for transfer/change, while force describes an interaction.'},
  {code:'heat_equals_temperature',severity:3,patterns:[/heat.{0,20}(is|equals|means).{0,20}temperature/i,/temperature.{0,20}(is|equals).{0,20}amount.{0,10}heat/i],remediation:'Repair thermal concepts: temperature characterizes thermal state; heat is energy transferred because of temperature difference.'},
];

export function diagnoseReasoning(conceptId:string,reasoning=''):DiagnosticFinding[]{
  getConcept(conceptId);
  if(!reasoning.trim())return[];
  const findings:DiagnosticFinding[]=[];
  for(const rule of RULES){
    const pattern=rule.patterns.find(p=>p.test(reasoning));
    if(pattern)findings.push({code:rule.code,severity:rule.severity,evidence:pattern.source,remediation:rule.remediation});
  }
  return findings;
}

export function mergeDiagnosticCodes(conceptId:string,reasoning:string|null|undefined,explicitCodes:readonly string[]=[],explicitSeverity=1):DiagnosticFinding[]{
  const inferred=diagnoseReasoning(conceptId,reasoning??'');
  const byCode=new Map(inferred.map(f=>[f.code,f]));
  for(const code of explicitCodes){
    const existing=byCode.get(code);
    if(existing)byCode.set(code,{...existing,severity:Math.max(existing.severity,explicitSeverity)});
    else byCode.set(code,{code,severity:explicitSeverity,evidence:'Explicitly tagged by the learning flow.',remediation:'Route to the targeted remediation associated with this misconception code.'});
  }
  return[...byCode.values()];
}
