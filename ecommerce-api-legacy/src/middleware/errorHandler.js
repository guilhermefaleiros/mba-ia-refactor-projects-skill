const { AppError } = require('../utils/errors');
const logger = require('../utils/logger');

function errorHandler(err, req, res, next) {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({ erro: err.message, sucesso: false });
  }

  logger.error('Unhandled exception', {
    path: req.path,
    method: req.method,
    message: err.message,
  });

  return res.status(500).json({ erro: 'Erro interno do servidor', sucesso: false });
}

module.exports = { errorHandler };
