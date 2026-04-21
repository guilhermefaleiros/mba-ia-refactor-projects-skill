const express = require('express');
const { config } = require('../config');
const { requireAuth } = require('../middleware/auth');
const checkoutController = require('../controllers/checkoutController');

const router = express.Router();

const middlewares = [];
if (config.app.checkoutRequiresAuth) {
  middlewares.push(requireAuth);
}

router.post('/checkout', ...middlewares, async (req, res, next) => {
  try {
    const { usr, eml, pwd, c_id: courseId, card } = req.body;

    if (!usr || !eml || !courseId || !card) {
      return res.status(400).send('Bad Request');
    }

    const result = await checkoutController.checkout({
      userName: usr,
      email: eml,
      password: pwd,
      courseId,
      cardNumber: card,
    });

    return res.status(200).json(result);
  } catch (err) {
    return next(err);
  }
});

module.exports = router;
