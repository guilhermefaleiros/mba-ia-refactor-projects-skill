const { run } = require('./database');

async function createEnrollment(userId, courseId) {
  const result = await run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
  return result.lastID;
}

async function createPayment(enrollmentId, amount, status) {
  await run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [enrollmentId, amount, status]);
}

async function createAuditLog(action) {
  await run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
}

module.exports = { createEnrollment, createPayment, createAuditLog };
