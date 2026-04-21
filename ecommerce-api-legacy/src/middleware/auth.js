const { config } = require('../config');

function extractBearerToken(headerValue) {
  if (!headerValue || !headerValue.startsWith('Bearer ')) {
    return null;
  }

  return headerValue.slice('Bearer '.length).trim();
}

function requireAuth(req, res, next) {
  const token = extractBearerToken(req.headers.authorization);

  if (!token || token !== config.security.adminApiToken) {
    return res.status(401).json({ erro: 'Não autorizado', sucesso: false });
  }

  return next();
}

module.exports = { requireAuth };
