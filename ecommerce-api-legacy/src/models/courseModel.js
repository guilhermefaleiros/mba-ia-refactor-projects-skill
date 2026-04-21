const { get } = require('./database');

async function findActiveCourseById(courseId) {
  return get('SELECT id, title, price FROM courses WHERE id = ? AND active = 1', [courseId]);
}

module.exports = { findActiveCourseById };
