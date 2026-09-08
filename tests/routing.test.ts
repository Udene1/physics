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
  db.db.prepare('INSERT INTO reviews(student_id,concept_id,due_at,interval_days,repetitions) VALUES(?,?,?,?,?)').run(student,'arithmetic','2000-01-01T00:00:00.000Z',1,0);
  const action = engine.nextAction(student);
  assert.equal(action.kind, 'review');
  assert.equal(action.conceptId, 'arithmetic');
  db.close();
});
