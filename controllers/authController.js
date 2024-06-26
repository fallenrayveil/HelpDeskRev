require('dotenv').config();
const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const db = require('../config/dbconfig');
const verifyToken = require('../middleware/authMiddleware');
const jwtSecret = process.env.JWT_SECRET;

const router = express.Router();

// Register User
const postRegister = (req, res) => {
  const { name, email, password } = req.body;

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
      return res.status(400).json({
          error: true,
          message: 'Invalid email format'
      });
  }

  if (password.length < 8) {
      return res.status(400).json({
          error: true,
          message: 'Password must be at least 8 characters long'
      });
  }

  const checkEmailQuery = 'SELECT * FROM users WHERE email = ?';
  db.query(checkEmailQuery, [email], (err, results) => {
      if (err) {
          console.error(err);
          return res.status(500).json({
              error: true,
              message: 'There is an error'
          });
      }

      if (results.length > 0) {
          return res.status(400).json({
              error: true,
              message: 'Email is registered'
          });
      }

      bcrypt.hash(password, 10, (err, hashedPassword) => {
          if (err) {
              console.error(err);
              return res.status(500).json({
                  error: true,
                  message: 'There is an error'
              });
          }

          const insertUserQuery = 'INSERT INTO users (name, email, password) VALUES (?, ?, ?)';
          db.query(insertUserQuery, [name, email, hashedPassword], (err) => {
              if (err) {
                  console.error(err);
                  return res.status(500).json({
                      error: true,
                      message: 'There is an error'
                  });
              }

              res.status(201).json({
                  error: false,
                  message: 'User Created'
              });
          });
      });
  });
};

// Login User
const postLogin = (req, res) => {
  const { email, password } = req.body;

  const findUserQuery = 'SELECT * FROM users WHERE email = ?';
  db.query(findUserQuery, [email], async (err, results) => {
      if (err) {
          console.error(err);
          return res.status(500).json({
              error: true,
              message: 'There is an error'
          });
      }

      if (results.length === 0 || !(await bcrypt.compare(password, results[0].password))) {
          return res.status(401).json({
              error: true,
              message: 'Email or password is incorrect'
          });
      }
      console.log(jwtSecret);
      const token = jwt.sign(
          {
              user_id: results[0].user_id,
              email: results[0].email
          },
          jwtSecret,
          { expiresIn: '7d' }
      );

      res.json({
          error: false,
          message: 'Success',
          loginResult: {
              userId: results[0].user_id,
              name: results[0].name,
              token: token
          }
      });
  });
};

// Get User Profile
const getProfile = (req, res) => {
  const userId = req.user.user_id;
  const getUserProfileQuery = 'SELECT name, email FROM users WHERE user_id = ?';

  db.query(getUserProfileQuery, [userId], (err, results) => {
      if (err) {
          console.error(err);
          return res.status(500).json({
              error: true,
              message: 'There is an error'
          });
      }

      if (results.length === 0) {
          return res.status(404).json({
              error: true,
              message: 'User not found'
          });
      }

      const { name, email } = results[0];
      res.json({ name, email });
  });
};

module.exports = { 
postRegister,
postLogin,
getProfile
};