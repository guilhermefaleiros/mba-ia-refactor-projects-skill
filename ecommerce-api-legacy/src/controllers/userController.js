const { AppError } = require('../utils/errors');
const userModel = require('../models/userModel');

async function deleteUser(userId) {
  const result = await userModel.deleteUserById(userId);

  if (result.changes === 0) {
    throw new AppError('Usuário não encontrado', 404);
  }

  return {
    msg: 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.',
  };
}

module.exports = { deleteUser };
