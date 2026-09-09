import test from 'node:test';
import assert from 'node:assert/strict';
import { LearningEngine } from '../src/learning-engine.js';
import { LearningStore } from '../src/store.js';

test('structured attempt persists reasoning evidence and misconception state', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('Learner');
  const engine = new LearningEngine(store);
  engine.start(student);
  const snapshot = engine.recordStructuredAttempt(student, 'forces', {correct:false, reasoning:'The object is moving, so it must have a force pushing it forward.'});
  assert.equal(snapshot.activeMisconceptions[0]?.code, 'force_causes_motion');
  assert.equal(snapshot.interventionQueue[0]?.stage, 'discrimination');
  store.close();
});

test('repeated misconception evidence accumulates instead of replacing history', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('History learner');
  const engine = new LearningEngine(store);
  engine.start(student);
  engine.recordStructuredAttempt(student, 'forces', {correct:false, reasoning:'Moving means a force is needed.'});
  engine.recordStructuredAttempt(student, 'forces', {correct:false, reasoning:'Moving means a force is needed.'});
  const misconception = store.listMisconceptions(student)[0]!;
  assert.equal(misconception.occurrences, 2);
  store.close();
});

test('lesson and problem resume survives a new engine instance', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('Resume learner');
  const engine = new LearningEngine(store);
  engine.start(student);
  engine.saveResume(student, 'lesson-motion-1', 'problem-motion-3', 4, {draft:'v = d/t', selectedStep:2});
  const resumed = new LearningEngine(store).snapshot(student).resume;
  assert.equal(resumed?.lessonId, 'lesson-motion-1');
  assert.equal(resumed?.problemId, 'problem-motion-3');
  assert.equal(resumed?.step, 4);
  assert.deepEqual(JSON.parse(resumed?.stateJson ?? '{}'), {draft:'v = d/t', selectedStep:2});
  store.close();
});

test('resolving a misconception requires repeated positive repair evidence', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('Learner');
  const engine = new LearningEngine(store);
  engine.start(student);
  const snapshot = engine.recordStructuredAttempt(student, 'arithmetic', {correct:false, misconceptionCodes:['ratio_additive']});
  const id = snapshot.activeMisconceptions[0]!.id;
  assert.throws(() => engine.resolveMisconception(student, id), /repeated positive repair evidence/);
  assert.equal(store.listMisconceptions(student)[0]?.status, 'active');
  store.close();
});
