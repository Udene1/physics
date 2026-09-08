import test from 'node:test';
import assert from 'node:assert/strict';
import { LearningStore } from '../src/store.js';
import { LearningEngine } from '../src/learning-engine.js';
import { estimateMastery } from '../src/evidence.js';

test('lesson catalog persists exact learner position through engine APIs', () => {
  const db = new LearningStore(':memory:');
  const student = db.ensureStudent('Lesson learner');
  const engine = new LearningEngine(db);
  engine.start(student);
  engine.placeByDemonstratedMastery(student, { arithmetic: 100, measurement: 100, graphs: 100 });
  const lesson = engine.lesson(student, 'motion-from-change');
  assert.equal(lesson.steps.length, 6);
  const resume = engine.advanceLesson(student, lesson.id, 2);
  assert.equal(resume.lessonId, lesson.id);
  assert.equal(resume.step, 2);
  assert.throws(() => engine.advanceLesson(student, lesson.id, 99), /outside the lesson/);
  db.close();
});

test('evidence estimates use repeated weighted evidence rather than one score', () => {
  const estimates = estimateMastery([
    { id: 1, studentId: 1, conceptId: 'motion', kind: 'problem', value: 100, note: '', createdAt: '' },
    { id: 2, studentId: 1, conceptId: 'motion', kind: 'problem', value: 0, note: '', createdAt: '' },
    { id: 3, studentId: 1, conceptId: 'motion', kind: 'transfer', value: 100, note: '', createdAt: '' },
  ]);
  assert.equal(estimates[0]?.conceptId, 'motion');
  assert.equal(estimates[0]?.score, 69.4);
  assert.equal(estimates[0]?.evidenceCount, 3);
});

test('engineering challenge unlocks only after demonstrated physics mastery', () => {
  const db = new LearningStore(':memory:');
  const student = db.ensureStudent('Builder');
  const engine = new LearningEngine(db);
  engine.start(student);
  assert.equal(engine.engineeringChallenges(student).length, 0);
  engine.placeByDemonstratedMastery(student, { measurement: 100, motion: 100 });
  assert.ok(engine.engineeringChallenges(student).some(c => c.id === 'motion-speed-meter'));
  assert.throws(() => engine.engineeringChallenge(student, 'force-cart'), /locked/);
  db.close();
});

test('resume rejects a problem from a different concept', () => {
  const db = new LearningStore(':memory:');
  const student = db.ensureStudent('Resume');
  const engine = new LearningEngine(db);
  engine.start(student);
  engine.placeByDemonstratedMastery(student, { arithmetic: 100, measurement: 100, graphs: 100 });
  assert.throws(() => engine.saveResume(student, 'motion-from-change', 'forces-net-force', 0), /different.*concept|belong/);
  db.close();
});
