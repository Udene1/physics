import assert from 'node:assert/strict';
import test from 'node:test';
import { teacherDashboardHtml } from '../src/teacher-dashboard.js';

test('teacher dashboard exposes classroom intelligence controls without embedding credentials', () => {
  const html = teacherDashboardHtml();
  assert.match(html, /Vita Learning Intelligence/);
  assert.match(html, /x-vita-teacher-key/);
  assert.match(html, /Class bottlenecks/);
  assert.match(html, /Who needs attention/);
  assert.doesNotMatch(html, /VITA_TEACHER_API_KEY/);
});
