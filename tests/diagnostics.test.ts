import test from 'node:test';
import assert from 'node:assert/strict';
import { diagnoseReasoning, mergeDiagnosticCodes } from '../src/diagnostics.js';

test('diagnostics infer a physics misconception from reasoning instead of relying on a pre-tagged code', () => {
  const findings = diagnoseReasoning('forces', 'The object is moving, so it must have a force pushing it forward.');
  assert.equal(findings.length, 1);
  assert.equal(findings[0]?.code, 'force_causes_motion');
  assert.equal(findings[0]?.severity, 4);
  assert.match(findings[0]?.remediation ?? '', /velocity|acceleration/i);
});

test('diagnostics can combine inferred and explicit evidence without duplicate codes', () => {
  const findings = mergeDiagnosticCodes(
    'forces',
    'The object is moving, so it must have a force pushing it forward.',
    ['force_causes_motion'],
    2,
  );
  assert.equal(findings.length, 1);
  assert.equal(findings[0]?.severity, 4);
});

test('explicit misconception codes remain usable when reasoning is unavailable', () => {
  const findings = mergeDiagnosticCodes('arithmetic', null, ['ratio_additive'], 3);
  assert.equal(findings.length, 1);
  assert.equal(findings[0]?.code, 'ratio_additive');
  assert.equal(findings[0]?.severity, 3);
});

test('diagnostics reject unknown concepts rather than silently producing learner state', () => {
  assert.throws(() => diagnoseReasoning('not-a-concept', 'some reasoning'));
});
