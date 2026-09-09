import { createServer } from 'node:http';
import { LearningEngine } from './learning-engine.js';
import { LearningStore } from './store.js';
import { getRemediationProblem } from './interventions.js';
import { getReviewProblemForConcept } from './reviews.js';
import { getConcept, validateCurriculum } from './curriculum.js';
import { getPracticeProblem, getPracticeProblemForConcept } from './practice.js';
import { evaluatePractice } from './practice-evaluator.js';

validateCurriculum();
const store = new LearningStore();
const engine = new LearningEngine(store);
const port = Number(process.env.VITA_API_PORT ?? 4310);

const json = (status: number, body: unknown) => ({ status, body: JSON.stringify(body) });
function student(name: string | null): number {
  const nickname = name?.trim();
  if (!nickname) throw new Error('student is required');
  return store.ensureStudent(nickname);
}
function readBody(req: import('node:http').IncomingMessage): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    let raw = '';
    req.setEncoding('utf8');
    req.on('data', chunk => { raw += chunk; if (raw.length > 1_000_000) reject(new Error('request body too large')); });
    req.on('end', () => { try { resolve(raw ? JSON.parse(raw) : {}); } catch { reject(new Error('invalid JSON')); } });
    req.on('error', reject);
  });
}
async function route(req: import('node:http').IncomingMessage, res: import('node:http').ServerResponse) {
  let result = json(500, { error: 'request failed' });
  try {
    const url = new URL(req.url ?? '/', `http://${req.headers.host ?? '127.0.0.1'}`);
    if (req.method === 'GET' && url.pathname === '/health') result = json(200, { status: 'ok', service: 'vita-adaptive-engine' });
    else if (req.method === 'GET' && url.pathname === '/v1/snapshot') { const id = student(url.searchParams.get('student')); result = json(200, engine.start(id)); }
    else if (req.method === 'GET' && url.pathname === '/v1/timeline') { const id = student(url.searchParams.get('student')); result = json(200, { events: engine.timeline(id) }); }
    else if (req.method === 'GET' && url.pathname === '/v1/practice') {
      const id = student(url.searchParams.get('student')); const snapshot = engine.start(id);
      const requested = url.searchParams.get('problemId');
      const problem = requested ? getPracticeProblem(requested) : getPracticeProblemForConcept(snapshot.currentConcept ?? snapshot.nextConcept ?? 'forces');
      result = json(200, { problem: problem ?? null, snapshot });
    } else if (req.method === 'POST' && url.pathname === '/v1/practice') {
      const body = await readBody(req); const id = student(typeof body.student === 'string' ? body.student : null);
      if (typeof body.problemId !== 'string') throw new Error('problemId is required');
      const problem = getPracticeProblem(body.problemId);
      if (typeof body.reasoning !== 'string' || typeof body.answer !== 'string') throw new Error('reasoning and answer are required');
      const evaluation = evaluatePractice(problem, body.reasoning, body.answer);
      const snapshot = engine.recordStructuredAttempt(id, problem.conceptId, {
        correct: evaluation.correct,
        reasoning: body.reasoning,
        problemId: problem.id,
        confidence: typeof body.confidence === 'number' ? body.confidence : null,
        hintUsed: body.hintUsed === true,
        durationSeconds: typeof body.durationSeconds === 'number' ? body.durationSeconds : null,
      });
      result = json(200, { evaluation, snapshot });
    } else if (req.method === 'POST' && url.pathname === '/v1/attempt') {
      const body = await readBody(req); const id = student(typeof body.student === 'string' ? body.student : null);
      if (typeof body.conceptId !== 'string') throw new Error('conceptId is required');
      getConcept(body.conceptId);
      if (typeof body.reasoning !== 'string') throw new Error('reasoning is required');
      if (typeof body.correct !== 'boolean') throw new Error('correct must be a boolean');
      const attempt: Parameters<LearningEngine['recordStructuredAttempt']>[2] = {
        correct: body.correct,
        reasoning: body.reasoning,
        problemId: typeof body.problemId === 'string' ? body.problemId : null,
        confidence: typeof body.confidence === 'number' ? body.confidence : null,
        hintUsed: body.hintUsed === true,
        durationSeconds: typeof body.durationSeconds === 'number' ? body.durationSeconds : null,
      };
      const misconceptionCodes = Array.isArray(body.misconceptionCodes)
        ? body.misconceptionCodes.filter((x): x is string => typeof x === 'string')
        : undefined;
      if (misconceptionCodes !== undefined) attempt.misconceptionCodes = misconceptionCodes;
      if (typeof body.misconceptionSeverity === 'number') attempt.misconceptionSeverity = body.misconceptionSeverity;
      result = json(200, engine.recordStructuredAttempt(id, body.conceptId, attempt));
    } else if (req.method === 'GET' && url.pathname === '/v1/intervention') {
      const id = student(url.searchParams.get('student')); const intervention = engine.nextIntervention(id);
      result = json(200, intervention ? { intervention, problem: getRemediationProblem(intervention.problemId), snapshot: engine.snapshot(id) } : { intervention: null, snapshot: engine.snapshot(id) });
    } else if (req.method === 'POST' && url.pathname === '/v1/remediation') {
      const body = await readBody(req); const id = student(typeof body.student === 'string' ? body.student : null);
      const interventionId = Number(body.interventionId);
      if (!Number.isInteger(interventionId)) throw new Error('interventionId must be an integer');
      if (typeof body.reasoning !== 'string' || typeof body.answer !== 'string') throw new Error('reasoning and answer are required');
      result = json(200, engine.submitRemediationAttempt(id, interventionId, { reasoning: body.reasoning, answer: body.answer, confidence: typeof body.confidence === 'number' ? body.confidence : null, hintUsed: body.hintUsed === true, durationSeconds: typeof body.durationSeconds === 'number' ? body.durationSeconds : null }));
    } else if (req.method === 'GET' && url.pathname === '/v1/review') {
      const id = student(url.searchParams.get('student')); const review = engine.nextReview(id); const problem = review ? getReviewProblemForConcept(review.conceptId) : undefined;
      result = json(200, { review: review ?? null, problem: problem ?? null, snapshot: engine.snapshot(id) });
    } else if (req.method === 'POST' && url.pathname === '/v1/review') {
      const body = await readBody(req); const id = student(typeof body.student === 'string' ? body.student : null);
      if (typeof body.reasoning !== 'string' || typeof body.answer !== 'string') throw new Error('reasoning and answer are required');
      result = json(200, engine.submitReviewAttempt(id, { reasoning: body.reasoning, answer: body.answer, confidence: typeof body.confidence === 'number' ? body.confidence : null, hintUsed: body.hintUsed === true, durationSeconds: typeof body.durationSeconds === 'number' ? body.durationSeconds : null }));
    } else result = json(404, { error: 'not_found' });
  } catch (error) {
    result = json(400, { error: error instanceof Error ? error.message : 'request failed' });
  }
  res.writeHead(result.status, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
  res.end(result.body);
}
const server = createServer((req, res) => { void route(req, res); });
server.listen(port, '127.0.0.1', () => console.log(`Vita adaptive API listening on 127.0.0.1:${port}`));
const shutdown = () => { server.close(() => { store.close(); process.exit(0); }); };
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
