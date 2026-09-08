import { LearningEngine } from './learning-engine.js';
import { LearningStore } from './store.js';
import { validateCurriculum } from './curriculum.js';

validateCurriculum();
const store = new LearningStore();
const studentId = store.ensureStudent(process.env.VITA_STUDENT ?? 'Guest');
const engine = new LearningEngine(store);
const snapshot = engine.start(studentId);
console.log(`Vita — adaptive physics learning`);
console.log(`Student: ${process.env.VITA_STUDENT ?? 'Guest'} (${studentId})`);
console.log(`Status: ${snapshot.status}`);
console.log(`Next physics concept: ${snapshot.nextConcept ?? 'none'}`);
console.log(`State is persisted in SQLite; the conversation is not the source of truth.`);
store.close();
