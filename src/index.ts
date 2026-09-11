import { createPostgresPool } from './infrastructure/postgres.js';
import { runMigrations } from './infrastructure/migrate.js';
import { PostgresLearningStore } from './infrastructure/postgres-store.js';
import { PostgresLearningEngine } from './application/postgres-learning-engine.js';
import { validateCurriculum } from './curriculum.js';

validateCurriculum();
const pool=createPostgresPool();
try {
  await runMigrations(pool);
  const store=new PostgresLearningStore(pool);
  const studentId=await store.ensureStudent(process.env.VITA_STUDENT??'Guest');
  const engine=new PostgresLearningEngine(store);
  const snapshot=await engine.start(studentId);
  console.log('Vita — evidence-driven adaptive physics learning');
  console.log(`Student: ${process.env.VITA_STUDENT??'Guest'} (${studentId})`);
  console.log(`Status: ${snapshot.status}`);
  console.log(`Next physics concept: ${snapshot.nextConcept??'none'}`);
  console.log('State is persisted in PostgreSQL; the conversation is not the source of truth.');
} finally {
  await pool.end();
}
