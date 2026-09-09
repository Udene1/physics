import test from 'node:test';
import assert from 'node:assert/strict';
import { LearningEngine } from '../src/learning-engine.js';
import { LearningStore } from '../src/store.js';

test('a due review evaluates reasoning and schedules the next retrieval from demonstrated performance', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('Retrieval learner');
  const engine = new LearningEngine(store);
  engine.start(student);
  const reference = new Date(Date.now() - 3 * 86400000);
  store.scheduleReview(student, 'energy', 1, reference);
  const problem = engine.getReviewProblem(student)!;
  assert.equal(problem.id, 'energy-review-1');
  const result = engine.submitReviewAttempt(student, { correct: true, reasoning: 'Force is an interaction measured in N. Work transfers energy through displacement. W = Fd = 20(2.5) = 50 J. N and J are different units.', answer: '50 J' });
  assert.equal(result.outcome, 'retained');
  assert.equal(result.checkpointScore, 1);
  assert.equal(result.snapshot.dueReviews.length, 0);
  assert.equal(result.snapshot.mastery.energy, 100);
  store.close();
});

test('a failed review reopens the misconception and routes the learner back to targeted repair', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('Recovery learner');
  const engine = new LearningEngine(store);
  engine.start(student);
  const reference = new Date(Date.now() - 3 * 86400000);
  store.scheduleReview(student, 'energy', 1, reference);
  const result = engine.submitReviewAttempt(student, { correct: false, reasoning: 'The force is 50 J because work and force are the same thing.', answer: '50 J' });
  assert.equal(result.outcome, 'misconception_reopened');
  assert.equal(result.snapshot.activeMisconceptions[0]?.code, 'energy_as_force');
  assert.equal(result.snapshot.selectedIntervention?.stage, 'discrimination');
  assert.equal(result.snapshot.selectedIntervention?.problemId, 'energy-force-discrimination-1');
  store.close();
});
