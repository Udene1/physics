import test from 'node:test';
import assert from 'node:assert/strict';
import { CURRICULUM, getConcept, learningFrontier, missingRequirements, validateCurriculum } from '../src/curriculum.js';

test('curriculum validates with five physics domains', () => { validateCurriculum(); const domains = new Set(CURRICULUM.filter(c => c.domain !== 'mathematics' && c.domain !== 'engineering').map(c => c.domain)); assert.deepEqual([...domains].sort(), ['electricity_magnetism','mechanics','modern_physics','thermal_physics','waves_optics'].sort()); });
test('modern physics has independent specializations', () => { assert.equal(getConcept('relativity').domain,'modern_physics'); assert.equal(getConcept('quantum').domain,'modern_physics'); assert.equal(getConcept('atomic_nuclear').domain,'modern_physics'); });
test('math is a dependency layer, not the learning spine', () => { const mastery={arithmetic:100,algebra:100,geometry:100,graphs:100,vectors:100}; assert.ok(missingRequirements(mastery,'motion').length === 0); assert.ok(learningFrontier(mastery).some(c => c.id === 'motion')); });
test('weak prerequisites block a physics concept', () => { assert.ok(missingRequirements({arithmetic:100},'motion').includes('measurement')); });
