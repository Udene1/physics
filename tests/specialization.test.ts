import test from 'node:test';
import assert from 'node:assert/strict';
import { LearningStore } from '../src/store.js';
import { LearningEngine } from '../src/learning-engine.js';

test('Modern Physics specialization requires its own prerequisites and survives reload', () => {
  const db = new LearningStore(':memory:');
  const student = db.ensureStudent('Modern');
  const engine = new LearningEngine(db);
  engine.start(student);
  assert.throws(() => engine.selectModernSpecialization(student, 'relativity'), /requirements/);
  engine.placeByDemonstratedMastery(student, { arithmetic:100, measurement:100, graphs:100, motion:100, vectors:100, algebra:100, fields:100 });
  engine.selectModernSpecialization(student, 'relativity');
  assert.equal(new LearningEngine(db).modernSpecialization(student), 'relativity');
  db.close();
});

test('atomic nuclear specialization is distinct from quantum and follows quantum', () => {
  const db = new LearningStore(':memory:');
  const student = db.ensureStudent('Atomic');
  const engine = new LearningEngine(db);
  engine.start(student);
  assert.throws(() => engine.selectModernSpecialization(student, 'atomic_nuclear'), /requirements/);
  db.placeMastery(student, 'waves', 100);
  db.placeMastery(student, 'fields', 100);
  db.placeMastery(student, 'motion', 100);
  db.placeMastery(student, 'arithmetic', 100);
  db.placeMastery(student, 'graphs', 100);
  db.placeMastery(student, 'algebra', 100);
  db.placeMastery(student, 'quantum', 100);
  engine.selectModernSpecialization(student, 'atomic_nuclear');
  assert.equal(engine.modernSpecialization(student), 'atomic_nuclear');
  db.close();
});
