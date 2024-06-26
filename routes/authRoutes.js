const express = require('express');
const authController = require('../controllers/authController');
const verifyToken = require('../middleware/authMiddleware');

const router = express.Router();

router.post('/register', authController.postRegister);
router.post('/login', authController.postLogin);
router.get('/profile', verifyToken, authController.getProfile);

module.exports = router;