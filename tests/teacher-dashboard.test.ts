import assert from 'node:assert/strict';
import test from 'node:test';
import { teacherDashboardHtml } from '../src/teacher-dashboard.js';

test('teacher dashboard is staff-scoped and discovers authorized classrooms', () => {
  const html = teacherDashboardHtml();
  assert.match(html, /Vita Learning Intelligence/);
  assert.match(html, /x-vita-staff-id/);
  assert.match(html, /\/v1\/teacher\/me/);
  assert.match(html, /\/v1\/teacher\/classrooms/);
  assert.match(html, /Select an authorized class/);
  assert.match(html, /Class bottlenecks/);
  assert.match(html, /Who needs attention/);
  assert.doesNotMatch(html, /x-vita-teacher-key/);
  assert.doesNotMatch(html, /VITA_TEACHER_API_KEY/);
});
