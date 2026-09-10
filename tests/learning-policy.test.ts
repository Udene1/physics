import assert from 'node:assert/strict';
import test from 'node:test';
import { REPAIR_POLICY, calculateReviewSchedule, hasDemonstratedRepair } from '../src/learning-policy.js';

test('repair requires repeated positive evidence and bounded confidence', () => {
  assert.equal(hasDemonstratedRepair(undefined), false);
  assert.equal(hasDemonstratedRepair({ positiveEvidence: 1, confidence: 0 }), false);
  assert.equal(hasDemonstratedRepair({ positiveEvidence: REPAIR_POLICY.minimumPositiveEvidence, confidence: REPAIR_POLICY.maximumConfidenceForResolution }), true);
  assert.equal(hasDemonstratedRepair({ positiveEvidence: 3, confidence: REPAIR_POLICY.maximumConfidenceForResolution + 1 }), false);
});

test('first strong review schedules a one-day retrieval', () => {
  const now = new Date('2026-01-01T00:00:00.000Z');
  const result = calculateReviewSchedule(1, undefined, now);
  assert.equal(result.intervalDays, 1);
  assert.equal(result.streak, 1);
  assert.equal(result.dueAt.toISOString(), '2026-01-02T00:00:00.000Z');
});

test('strong reviews expand retrieval interval while weak reviews reset it', () => {
  const now = new Date('2026-01-10T00:00:00.000Z');
  const expanded = calculateReviewSchedule(0.9, { intervalDays: 2, streak: 2 }, now);
  assert.equal(expanded.intervalDays, 6);
  assert.equal(expanded.streak, 3);
  assert.equal(expanded.dueAt.toISOString(), '2026-01-16T00:00:00.000Z');

  const reset = calculateReviewSchedule(0.4, { intervalDays: 30, streak: 5 }, now);
  assert.equal(reset.intervalDays, 1);
  assert.equal(reset.streak, 0);
  assert.equal(reset.dueAt.toISOString(), '2026-01-11T00:00:00.000Z');
});

test('review interval is capped instead of growing without bound', () => {
  const now = new Date('2026-01-01T00:00:00.000Z');
  const result = calculateReviewSchedule(1, { intervalDays: 60, streak: 10 }, now);
  assert.equal(result.intervalDays, 90);
});
