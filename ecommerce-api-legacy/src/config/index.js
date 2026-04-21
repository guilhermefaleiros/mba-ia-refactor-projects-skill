const REQUIRED_ENV_VARS = ['APP_SECRET', 'ADMIN_API_TOKEN', 'PAYMENT_GATEWAY_KEY'];

const config = {
  app: {
    port: Number(process.env.PORT || 3000),
    checkoutRequiresAuth: (process.env.CHECKOUT_REQUIRES_AUTH || 'true').toLowerCase() === 'true',
  },
  database: {
    path: process.env.DATABASE_PATH || ':memory:',
  },
  security: {
    appSecret: process.env.APP_SECRET,
    adminApiToken: process.env.ADMIN_API_TOKEN,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
  },
};

function validateConfig() {
  const missing = REQUIRED_ENV_VARS.filter((name) => !process.env[name]);

  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
  }
}

module.exports = { config, validateConfig };
