import test from 'node:test';
import assert from 'node:assert/strict';
import { evaluateAnswer } from '../src/answer-evaluator.js';
import { getRemediationProblem } from '../src/interventions.js';
import { getReviewProblem } from '../src/reviews.js';

test('a numerically correct remediation answer is evaluated from the submitted answer', () => {
  const problem = getRemediationProblem('force-motion-transfer-1');
  const result = evaluateAnswer(problem, 'a = 2 m/s² east; v = 7 m/s east');
  assert.equal(result.correct, true);
  assert.deepEqual(result.missingCriteria, []);
});

test('an answer with the wrong physical quantity is rejected even when the client could claim success', () => {
  const problem = getRemediationProblem('energy-force-transfer-1');
  const result = evaluateAnswer(problem, '30 N');
  assert.equal(result.correct, false);
  assert.ok(result.missingCriteria.includes('force'));
});

test('review answers use the same structured correctness contract', () => {
  const problem = getReviewProblem('vectors-review-1');
  const result = evaluateAnswer(problem, '13 N at about 22.6° north of east');
  assert.equal(result.correct, true);
});
