const { AppError } = require('../utils/errors');
const logger = require('../utils/logger');
const { hashPassword } = require('../utils/security');
const { config } = require('../config');
const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const checkoutModel = require('../models/checkoutModel');

function resolvePaymentStatus(cardNumber) {
  if (!cardNumber || typeof cardNumber !== 'string') {
    throw new AppError('Invalid card', 400);
  }

  return cardNumber.startsWith('4') ? 'PAID' : 'DENIED';
}

async function checkout({ userName, email, password, courseId, cardNumber }) {
  const course = await courseModel.findActiveCourseById(courseId);
  if (!course) {
    throw new AppError('Curso não encontrado', 404);
  }

  let user = await userModel.findByEmail(email);
  if (!user) {
    if (!password) {
      throw new AppError('Password is required for new users', 400);
    }

    const hashedPassword = hashPassword(password);
    const userId = await userModel.createUser(userName, email, hashedPassword);
    user = { id: userId };
  }

  const paymentStatus = resolvePaymentStatus(cardNumber);
  if (paymentStatus === 'DENIED') {
    throw new AppError('Pagamento recusado', 400);
  }

  const enrollmentId = await checkoutModel.createEnrollment(user.id, course.id);
  await checkoutModel.createPayment(enrollmentId, course.price, paymentStatus);
  await checkoutModel.createAuditLog(`Checkout curso ${course.id} por ${user.id}`);

  logger.info('Checkout completed', {
    userId: user.id,
    courseId: course.id,
    enrollmentId,
    paymentGatewayConfigured: Boolean(config.security.paymentGatewayKey),
  });

  return {
    msg: 'Sucesso',
    enrollment_id: enrollmentId,
  };
}

module.exports = { checkout };
