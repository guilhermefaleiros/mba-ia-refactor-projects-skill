function log(level, message, context = {}) {
  const payload = {
    level,
    message,
    context,
    timestamp: new Date().toISOString(),
  };

  process.stdout.write(`${JSON.stringify(payload)}\n`);
}

module.exports = {
  info: (message, context) => log('info', message, context),
  error: (message, context) => log('error', message, context),
};
