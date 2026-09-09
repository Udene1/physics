import test from 'node:test';
import assert from 'node:assert/strict';
import { LearningEngine } from '../src/learning-engine.js';
import { LearningStore } from '../src/store.js';

test('structured attempt persists reasoning evidence and misconception state', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('Learner');
  const engine = new LearningEngine(store);
  engine.start(student);
  const snapshot = engine.recordStructuredAttempt(student, 'arithmetic', {
    correct: false,
    problemId: 'p-1',
    lessonId: 'l-1',
    reasoning: 'I treated the ratio as an addition.',
    confidence: 4,
    hintUsed: true,
    durationSeconds: 31,
    misconceptionCodes: ['ratio_additive'],
    misconceptionSeverity: 3,
  });
  assert.equal(snapshot.mastery.arithmetic, 0);
  assert.equal(snapshot.activeMisconceptions[0]?.code, 'ratio_additive');
  assert.equal(snapshot.activeMisconceptions[0]?.occurrences, 1);
  const row = store.db.prepare('SELECT reasoning, problem_id, lesson_id, confidence, hint_used, duration_seconds FROM evidence').get() as any;
  assert.equal(row.reasoning, 'I treated the ratio as an addition.');
  assert.equal(row.problem_id, 'p-1');
  assert.equal(row.lesson_id, 'l-1');
  assert.equal(row.confidence, 4);
  assert.equal(row.hint_used, 1);
  assert.equal(row.duration_seconds, 31);
  store.close();
});

test('repeated misconception evidence accumulates instead of replacing history', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('Learner');
  const engine = new LearningEngine(store);
  engine.start(student);
  engine.recordStructuredAttempt(student, 'arithmetic', {correct:false, misconceptionCodes:['ratio_additive']});
  const second = engine.recordStructuredAttempt(student, 'arithmetic', {correct:false, misconceptionCodes:['ratio_additive']});
  assert.equal(second.activeMisconceptions[0]?.occurrences, 2);
  assert.equal(store.db.prepare('SELECT COUNT(*) AS count FROM evidence').get()?.count, 2);
  store.close();
});

test('lesson and problem resume survives a new engine instance', () => {
  const store = new LearningStore(':memory:');
  const student = store.ensureStudent('Learner');
  const first = new LearningEngine(store);
  first.start(student);
  first.saveResume(student, 'lesson-motion-1', 'problem-motion-3', 4, {draft:'v = d/t', selectedStep:2});
  const second = new LearningEngine(store);
  const resume = second.snapshot(student).resume;
  assert.equal(resume?.lessonId, 'lesson-motion-1');
  assert.equal(resume?.problemId, 'problem-motion-3');
  assert.equal(resume?.step, 4);
  assert.deepEqual(JSON.parse(resume?.stateJson ?? '{}'), {draft:'v = d/t', selectedStep:2});
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
