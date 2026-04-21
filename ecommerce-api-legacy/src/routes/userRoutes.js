const express = require('express');
const userController = require('../controllers/userController');
const { requireAuth } = require('../middleware/auth');

const router = express.Router();

router.delete('/users/:id', requireAuth, async (req, res, next) => {
  try {
    const result = await userController.deleteUser(req.params.id);
    return res.send(result.msg);
  } catch (err) {
    return next(err);
  }
});

module.exports = router;
