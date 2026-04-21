const express = require('express');
const adminController = require('../controllers/adminController');
const { requireAuth } = require('../middleware/auth');

const router = express.Router();

router.get('/admin/financial-report', requireAuth, async (req, res, next) => {
  try {
    const result = await adminController.getFinancialReport();
    return res.json(result);
  } catch (err) {
    return next(err);
  }
});

module.exports = router;
