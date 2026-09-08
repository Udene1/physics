import test from 'node:test';
import assert from 'node:assert/strict';
import { LearningStore } from '../src/store.js';

test('repository transaction rolls back partial learner-state writes', () => {
  const db = new LearningStore(':memory:');
  const student = db.ensureStudent('Rollback');
  assert.throws(() => db.transaction(() => {
    db.addEvidence(student, 'motion', 'problem', 0, 'should roll back');
    db.addMisconception(student, 'motion', 'temporary', 'should roll back');
    throw new Error('forced failure');
  }), /forced failure/);
  assert.equal(db.db.prepare('SELECT COUNT(*) AS count FROM evidence WHERE student_id=?').get(student).count, 0);
  assert.equal(db.listOpenMisconceptions(student).length, 0);
  db.close();
});

test('mastery placement preserves attempt counters while changing demonstrated score', () => {
  const db = new LearningStore(':memory:');
  const student = db.ensureStudent('Placement');
  db.recordMastery(student, 'motion', false);
  db.setMastery(student, 'motion', 80);
  const row = db.db.prepare('SELECT score,attempts,correct FROM mastery WHERE student_id=? AND concept_id=?').get(student, 'motion') as {score:number;attempts:number;correct:number};
  assert.equal(row.score, 80);
  assert.equal(row.attempts, 1);
  assert.equal(row.correct, 0);
  db.close();
});
