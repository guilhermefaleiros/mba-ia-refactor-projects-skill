const crypto = require('crypto');

function hashPassword(plainPassword) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(plainPassword, salt, 64).toString('hex');
  return `${salt}:${hash}`;
}

function verifyPassword(plainPassword, storedHash) {
  const [salt, originalHash] = storedHash.split(':');
  const hash = crypto.scryptSync(plainPassword, salt, 64).toString('hex');
  return crypto.timingSafeEqual(Buffer.from(originalHash, 'hex'), Buffer.from(hash, 'hex'));
}

module.exports = { hashPassword, verifyPassword };
