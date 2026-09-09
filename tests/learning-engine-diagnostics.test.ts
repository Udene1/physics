import test from 'node:test';
import assert from 'node:assert/strict';
import { LearningEngine } from '../src/learning-engine.js';
import { LearningStore } from '../src/store.js';

test('recorded reasoning automatically creates a persisted misconception finding', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('Diagnostic learner');
  const engine = new LearningEngine(store);
  engine.start(student);

  const snapshot = engine.recordStructuredAttempt(student, 'forces', {
    correct: false,
    problemId: 'forces-1',
    reasoning: 'The object is moving, so it must have a force pushing it forward.',
  });

  assert.equal(snapshot.activeMisconceptions.length, 1);
  assert.equal(snapshot.activeMisconceptions[0]?.code, 'force_causes_motion');
  assert.equal(snapshot.activeMisconceptions[0]?.lastEvidenceId, 1);
  store.close();
});

test('diagnostic findings expose a concrete remediation path', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('Diagnostic learner');
  const engine = new LearningEngine(store);
  engine.start(student);

  const findings = engine.diagnoseAttempt('forces', 'No force means the object cannot keep moving.');
  assert.equal(findings[0]?.code, 'force_causes_motion');
  assert.match(findings[0]?.remediation ?? '', /velocity|acceleration/i);
  store.close();
});
