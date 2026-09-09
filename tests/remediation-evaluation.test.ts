import test from 'node:test';
import assert from 'node:assert/strict';
import { getRemediationProblem } from '../src/interventions.js';
import { evaluateRemediation } from '../src/remediation-evaluator.js';

test('force-motion transfer accepts complete physics reasoning', () => {
  const problem = getRemediationProblem('force-motion-transfer-1');
  const result = evaluateRemediation(
    problem,
    'F_net = ma gives a = 4/2 = 2 m/s² east. Then v = u + at = 3 + 2(2) = 7 m/s east. The force changes velocity through acceleration.',
    '2 m/s² east; 7 m/s east',
    true,
  );
  assert.deepEqual(result.missingCheckpoints, []);
  assert.equal(result.checkpointScore, 1);
  assert.equal(result.answerCorrect, true);
  assert.equal(result.verdict, 'repaired');
});
