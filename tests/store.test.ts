import test from 'node:test';
import assert from 'node:assert/strict';
import { LearningStore } from '../src/store.js';
import { LearningEngine } from '../src/learning-engine.js';

test('real SQLite learner state survives a new engine instance', () => { const db = new LearningStore(':memory:'); const student = db.ensureStudent('Ada'); const first = new LearningEngine(db); first.start(student); first.placeByDemonstratedMastery(student,{arithmetic:100,measurement:100}); first.recordAttempt(student,'motion',true,'correct velocity reasoning'); const second = new LearningEngine(db); const snapshot = second.snapshot(student); assert.equal(snapshot.mastery.motion,100); assert.equal(snapshot.status,'learning'); db.close(); });
test('recording mastery changes the durable learner model', () => { const db = new LearningStore(':memory:'); const student = db.ensureStudent('Test'); const engine = new LearningEngine(db); engine.start(student); const result = engine.recordAttempt(student,'arithmetic',true); assert.equal(result.mastery.arithmetic,100); db.close(); });
test('current concept cannot bypass requirements', () => { const db = new LearningStore(':memory:'); const student = db.ensureStudent('Test'); const engine = new LearningEngine(db); engine.start(student); assert.throws(() => engine.setCurrent(student,'forces'), /requirements/); db.close(); });
