import test from 'node:test';
import assert from 'node:assert/strict';
import { LearningEngine } from '../src/learning-engine.js';
import { LearningStore } from '../src/store.js';

test('a diagnosed misconception creates a targeted discrimination intervention', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('Adaptive learner');
  const engine = new LearningEngine(store);
  engine.start(student);
  const snapshot = engine.recordStructuredAttempt(student, 'forces', { correct: false, problemId: 'forces-1', reasoning: 'The object is moving, so it must have a force pushing it forward.' });
  assert.equal(snapshot.activeMisconceptions[0]?.code, 'force_causes_motion');
  assert.equal(snapshot.interventionQueue[0]?.stage, 'discrimination');
  assert.equal(snapshot.interventionQueue[0]?.prerequisiteConceptId, 'motion');
  assert.equal(snapshot.interventionQueue[0]?.problemId, 'force-motion-discrimination-1');
  store.close();
});

test('remediation requires reasoning checkpoints, not only a correct answer', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('Checkpoint learner');
  const engine = new LearningEngine(store);
  engine.start(student);
  engine.recordStructuredAttempt(student, 'forces', { correct:false, reasoning:'Moving means a force is needed.' });
  const intervention = engine.nextIntervention(student)!;
  const weak = engine.submitRemediationAttempt(student, intervention.id, { correct:true, reasoning:'0 N.', answer:'0 N' });
  assert.notEqual(weak.evaluation.verdict, 'repaired');
  const strong = engine.submitRemediationAttempt(student, intervention.id, { correct:true, reasoning:'The velocity is constant, so acceleration is zero. Using F_net = ma gives net force zero. A net force changes velocity by producing acceleration; it is not needed to sustain constant velocity.', answer:'0 N' });
  assert.equal(strong.evaluation.verdict, 'repaired');
  assert.equal(strong.evaluation.checkpointScore, 1);
  assert.equal(strong.snapshot.interventionQueue[0]?.stage, 'transfer');
  store.close();
});

test('persistent failure raises misconception confidence and successful transfer reduces it', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('Evidence learner');
  const engine = new LearningEngine(store);
  engine.start(student);
  engine.recordStructuredAttempt(student, 'forces', { correct:false, reasoning:'No force means the object cannot keep moving.' });
  const first = engine.nextIntervention(student)!;
  const before = store.getMisconceptionState(first.misconceptionId)!.confidence;
  const failed = engine.submitRemediationAttempt(student, first.id, { correct:false, reasoning:'Because it is moving, it needs force.', answer:'5 N' });
  const afterFailure = store.getMisconceptionState(first.misconceptionId)!.confidence;
  assert.equal(failed.evaluation.verdict, 'still_present');
  assert.ok(afterFailure > before);
  const repaired = engine.submitRemediationAttempt(student, first.id, { correct:true, reasoning:'Constant velocity means acceleration is zero. F_net = ma, so the net force is zero. Force changes velocity through acceleration, not by sustaining motion.', answer:'0 N' });
  const afterRepair = store.getMisconceptionState(first.misconceptionId)!.confidence;
  assert.equal(repaired.evaluation.verdict, 'repaired');
  assert.ok(afterRepair < afterFailure);
  store.close();
});

test('strong demonstrated repair creates performance-based spaced review', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('Review learner');
  const engine = new LearningEngine(store);
  engine.start(student);
  engine.recordStructuredAttempt(student, 'forces', { correct:false, reasoning:'Moving means a force is needed.' });
  const discrimination = engine.nextIntervention(student)!;
  engine.submitRemediationAttempt(student, discrimination.id, { correct:true, reasoning:'Constant velocity means acceleration is zero. F_net = ma, so net force is zero. A net force changes velocity by causing acceleration.', answer:'0 N' });
  const transfer = engine.nextIntervention(student)!;
  const result = engine.submitRemediationAttempt(student, transfer.id, { correct:true, reasoning:'F_net = ma gives a = 4/2 = 2 m/s² east. Then v = u + at = 3 + 2(2) = 7 m/s east. The force changes velocity through acceleration.', answer:'2 m/s² east; 7 m/s east' });
  assert.equal(result.evaluation.verdict, 'repaired');
  const reviews = store.listDueReviews(student, new Date(Date.now() + 2 * 86400000).toISOString());
  assert.equal(reviews.length, 1);
  assert.equal(reviews[0]?.conceptId, 'forces');
  assert.equal(reviews[0]?.intervalDays, 1);
  store.close();
});

test('a failed review reopens the diagnosed misconception and queues fresh discrimination', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('Retention learner');
  const engine = new LearningEngine(store);
  engine.start(student);
  engine.recordStructuredAttempt(student, 'forces', { correct:false, reasoning:'Moving means a force is needed.' });
  const discrimination = engine.nextIntervention(student)!;
  engine.submitRemediationAttempt(student, discrimination.id, { reasoning:'Constant velocity means acceleration is zero. F_net = ma, so net force is zero. Force changes velocity through acceleration, not by sustaining motion.', answer:'0 N' });
  const transfer = engine.nextIntervention(student)!;
  engine.submitRemediationAttempt(student, transfer.id, { reasoning:'F_net = ma gives a = 2 m/s² east. Then v = u + at = 7 m/s east. The force changes velocity through acceleration.', answer:'2 m/s² east; 7 m/s east' });
  const dueAt = new Date(Date.now() + 2 * 86400000);
  assert.equal(store.listDueReviews(student, dueAt.toISOString()).length, 1);
  const review = engine.submitReviewAttempt(student, { reasoning:'The cart is moving, so it needs a force to keep moving.', answer:'17 N east' }, dueAt);
  assert.equal(review.outcome, 'misconception_reopened');
  assert.equal(review.snapshot.activeMisconceptions.some(m => m.code === 'force_causes_motion'), true);
  assert.equal(review.snapshot.interventionQueue.some(i => i.stage === 'discrimination'), true);
  store.close();
});
