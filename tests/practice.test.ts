import test from 'node:test';
import assert from 'node:assert/strict';
import { getPracticeProblem } from '../src/practice.js';
import { evaluatePractice } from '../src/practice-evaluator.js';
import { LearningEngine } from '../src/learning-engine.js';
import { LearningStore } from '../src/store.js';

test('real practice problem requires both final answer and diagnostic reasoning', () => {
  const problem = getPracticeProblem('forces-1');
  const result = evaluatePractice(problem,
    'Constant velocity means zero acceleration. F_net = ma gives zero net force. A net force changes velocity through acceleration.',
    '0 N');
  assert.equal(result.verdict, 'correct');
  assert.equal(result.correct, true);
  assert.deepEqual(result.missingCheckpoints, []);
});

test('practice misconception reasoning is persisted and routes targeted repair', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('Practice learner');
  const engine = new LearningEngine(store);
  engine.start(student);
  const problem = getPracticeProblem('forces-1');
  const evaluation = evaluatePractice(problem, 'The object is moving, so it needs force.', '5 N');
  assert.equal(evaluation.verdict, 'misconception_detected');
  const snapshot = engine.recordStructuredAttempt(student, problem.conceptId, { correct: evaluation.correct, reasoning: 'The object is moving, so it needs force.', problemId: problem.id });
  assert.equal(snapshot.activeMisconceptions.some(m => m.code === 'force_causes_motion'), true);
  assert.equal(snapshot.selectedIntervention?.stage, 'discrimination');
  store.close();
});
