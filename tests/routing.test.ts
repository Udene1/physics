import test from 'node:test';
import assert from 'node:assert/strict';
import { LearningStore } from '../src/store.js';
import { LearningEngine } from '../src/learning-engine.js';

test('next action prioritizes misconception remediation over normal progression', () => {
  const db = new LearningStore(':memory:');
  const student = db.ensureStudent('Routing');
  const engine = new LearningEngine(db);
  engine.start(student);
  engine.placeByDemonstratedMastery(student, { arithmetic: 100, measurement: 100, graphs: 100 });
  engine.recordMisconception(student, 'motion', 'speed-wrong-model', 'Uses distance as speed');
  const action = engine.nextAction(student);
  assert.equal(action.kind, 'remediate');
  assert.equal(action.conceptId, 'motion');
  db.close();
});

test('next action schedules a due review before a new lesson', () => {
  const db = new LearningStore(':memory:');
  const student = db.ensureStudent('Review routing');
  const engine = new LearningEngine(db);
  engine.start(student);
  db.setMastery(student, 'arithmetic', 100);
  db.scheduleReview(student, 'arithmetic', false);
  const action = engine.nextAction(student);
  assert.equal(action.kind, 'review');
  assert.equal(action.conceptId, 'arithmetic');
  db.close();
});
