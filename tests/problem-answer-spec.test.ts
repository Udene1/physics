import test from 'node:test';
import assert from 'node:assert/strict';
import { getRemediationProblem } from '../src/interventions.js';
import { getReviewProblem } from '../src/reviews.js';
import { evaluateAnswer } from '../src/answer-evaluator.js';

test('structured numeric specs accept equivalent unit formatting and tolerance', () => {
  const problem = getRemediationProblem('direction-scalar-transfer-1');
  const result = evaluateAnswer(problem, 'The net force is 5.0 N, directed northeast.');
  assert.equal(result.correct, true);
  assert.deepEqual(result.missingCriteria, []);
});

test('structured specs reject correct magnitude with wrong units', () => {
  const problem = getRemediationProblem('energy-force-discrimination-1');
  const result = evaluateAnswer(problem, 'The work is 20 N. Force and work are different quantities.');
  assert.equal(result.correct, false);
  assert.ok(result.missingCriteria.includes('work'));
});

test('structured conceptual specs require the physical distinction, not just a number', () => {
  const problem = getReviewProblem('temperature-review-1');
  const result = evaluateAnswer(problem, 'The final state is 30 degrees and the hot object cools.');
  assert.equal(result.correct, false);
  assert.ok(result.missingCriteria.includes('thermal-state'));
  assert.ok(result.missingCriteria.includes('heat-transfer'));
});

test('review answers use the same structured evaluator as remediation answers', () => {
  const problem = getReviewProblem('vectors-review-1');
  const result = evaluateAnswer(problem, '13 N northeast, about 22.6 degrees north of east.');
  assert.equal(result.correct, true);
});
