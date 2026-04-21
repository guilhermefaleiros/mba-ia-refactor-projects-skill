const express = require('express');
const { config, validateConfig } = require('./config');
const { initDatabase } = require('./models/database');
const { errorHandler } = require('./middleware/errorHandler');
const checkoutRoutes = require('./routes/checkoutRoutes');
const adminRoutes = require('./routes/adminRoutes');
const userRoutes = require('./routes/userRoutes');
const logger = require('./utils/logger');

async function start() {
  validateConfig();
  await initDatabase();

  const app = express();
  app.use(express.json());

  app.use('/api', checkoutRoutes);
  app.use('/api', adminRoutes);
  app.use('/api', userRoutes);

  app.use(errorHandler);

  app.listen(config.app.port, () => {
    logger.info('Application started', { port: config.app.port });
  });
}

start().catch((err) => {
  logger.error('Startup failed', { message: err.message });
  process.exit(1);
});
