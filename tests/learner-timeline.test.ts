import test from 'node:test';
import assert from 'node:assert/strict';
import { LearningEngine } from '../src/learning-engine.js';
import { LearningStore } from '../src/store.js';

test('timeline reconstructs evidence, intervention, remediation and review events', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('Timeline learner');
  const engine = new LearningEngine(store);
  engine.start(student);

  engine.recordStructuredAttempt(student, 'forces', {
    correct: false,
    reasoning: 'The object is moving, so it needs force.',
  });
  const intervention = engine.nextIntervention(student)!;
  engine.submitRemediationAttempt(student, intervention.id, {
    reasoning: 'Constant velocity means zero acceleration. F_net = ma gives zero net force. A net force changes velocity through acceleration.',
    answer: '0 N',
  });

  const timeline = engine.timeline(student);
  const types = timeline.map(event => event.type);
  assert.ok(types.includes('evidence'));
  assert.ok(types.includes('intervention'));
  assert.ok(types.includes('remediation'));
  assert.ok(timeline.some(event => event.verdict === 'repaired'));
  assert.ok(timeline.every(event => event.conceptId === 'forces'));
  assert.ok(timeline.every(event => event.at.length > 0));
  store.close();
});
