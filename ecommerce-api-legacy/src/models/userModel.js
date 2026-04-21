const { get, run } = require('./database');

async function findByEmail(email) {
  return get('SELECT id, name, email, pass FROM users WHERE email = ?', [email]);
}

async function createUser(name, email, passwordHash) {
  const result = await run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
  return result.lastID;
}

async function deleteUserById(id) {
  return run('DELETE FROM users WHERE id = ?', [id]);
}

module.exports = { findByEmail, createUser, deleteUserById };
