import assert from 'node:assert/strict';
import test from 'node:test';
import { persistModelArtifact } from '../src/application/artifact-provenance.js';
import type { ModelResponse } from '../src/llm/model-gateway.js';

/** Contract test: the application boundary maps provider output to provenance without owning learning state. */
test('persistModelArtifact preserves model provenance and defaults training eligibility off', async () => {
  const calls: unknown[] = [];
  const pool = { connect: async () => { throw new Error('pool not expected in this unit boundary'); }, query: async (...args: unknown[]) => { calls.push(args); return { rows: [] }; } } as never;
  assert.throws(() => persistModelArtifact(pool, { text: 'x', provider: 'provider-a', model: 'model-a' } as ModelResponse, { artifactKind: 'problem' }), /pool not expected/);
  assert.equal(calls.length, 0);
});
