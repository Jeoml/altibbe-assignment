// src/routes/auth.js
const express = require('express');
const bcrypt = require('bcryptjs');
const { body, validationResult } = require('express-validator');
const { generateTokens, revokeToken, authenticateToken } = require('../middleware/auth');
const { asyncHandler } = require('../middleware/errorHandler');
const { sanitizeObject } = require('../middleware/security');
const db = require('../config/database');

const router = express.Router();

/**
 * @swagger
 * components:
 *   schemas:
 *     User:
 *       type: object
 *       properties:
 *         id:
 *           type: integer
 *           description: User ID
 *         email:
 *           type: string
 *           format: email
 *           description: User email
 *         company_name:
 *           type: string
 *           description: Company name
 *         first_name:
 *           type: string
 *           description: First name
 *         last_name:
 *           type: string
 *           description: Last name
 *         created_at:
 *           type: string
 *           format: date-time
 *           description: Account creation date
 *     AuthResponse:
 *       type: object
 *       properties:
 *         user:
 *           $ref: '#/components/schemas/User'
 *         access_token:
 *           type: string
 *           description: JWT access token
 *         refresh_token:
 *           type: string
 *           description: JWT refresh token
 *     RegisterRequest:
 *       type: object
 *       required:
 *         - email
 *         - password
 *         - company_name
 *         - first_name
 *         - last_name
 *       properties:
 *         email:
 *           type: string
 *           format: email
 *           description: User email
 *         password:
 *           type: string
 *           minLength: 8
 *           maxLength: 128
 *           description: Password (8-128 chars, must contain uppercase, lowercase, number, special char)
 *         company_name:
 *           type: string
 *           maxLength: 255
 *           description: Company name
 *         first_name:
 *           type: string
 *           maxLength: 100
 *           description: First name
 *         last_name:
 *           type: string
 *           maxLength: 100
 *           description: Last name
 *     LoginRequest:
 *       type: object
 *       required:
 *         - email
 *         - password
 *       properties:
 *         email:
 *           type: string
 *           format: email
 *           description: User email
 *         password:
 *           type: string
 *           description: User password
 *     Error:
 *       type: object
 *       properties:
 *         error:
 *           type: string
 *           description: Error message
 *         details:
 *           type: array
 *           items:
 *             type: object
 *           description: Validation error details
 */

// Registration validation
const validateRegistration = [
  body('email')
    .isEmail()
    .normalizeEmail()
    .withMessage('Valid email required'),
  
  body('password')
    .isLength({ min: 8, max: 128 })
    .withMessage('Password must be 8-128 characters')
    .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]/)
    .withMessage('Password must contain uppercase, lowercase, number, and special character'),
  
  body('company_name')
    .trim()
    .isLength({ min: 1, max: 255 })
    .withMessage('Company name required'),
  
  body('first_name')
    .trim()
    .isLength({ min: 1, max: 100 })
    .withMessage('First name required'),
  
  body('last_name')
    .trim()
    .isLength({ min: 1, max: 100 })
    .withMessage('Last name required')
];

// Login validation
const validateLogin = [
  body('email')
    .isEmail()
    .normalizeEmail()
    .withMessage('Valid email required'),
  
  body('password')
    .isLength({ min: 1 })
    .withMessage('Password required')
];

/**
 * @swagger
 * /api/auth/register:
 *   post:
 *     summary: Register a new user
 *     tags: [Authentication]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/RegisterRequest'
 *     responses:
 *       201:
 *         description: User registered successfully
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/AuthResponse'
 *       400:
 *         description: Validation failed
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       409:
 *         description: User already exists
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
// Register
router.post('/register', validateRegistration, asyncHandler(async (req, res) => {
  console.log('=== REGISTRATION ENDPOINT STARTED ===');
  console.log('📝 Received request body:', req.body);
  console.log('📋 Headers:', req.headers);
  
  // Check validation results
  console.log('🔍 Checking validation results...');
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    console.error('❌ VALIDATION FAILED:', errors.array());
    return res.status(400).json({ 
      error: 'Validation failed',
      details: errors.array()
    });
  }
  console.log('✅ Validation passed');

  // Sanitize data
  console.log('🧹 Sanitizing request data...');
  const sanitizedData = sanitizeObject(req.body);
  console.log('✅ Data sanitized:', {
    ...sanitizedData,
    password: '***hidden***' // Don't log the actual password
  });
  
  const { email, password, company_name, first_name, last_name } = sanitizedData;

  try {
    // Check if user exists
    console.log('🔍 Checking if user exists for email:', email);
    const existingUser = await db.query('SELECT id FROM users WHERE email = $1', [email]);
    console.log('📊 Database query result - existing users found:', existingUser.rows.length);
    
    if (existingUser.rows.length > 0) {
      console.log('❌ User already exists with email:', email);
      return res.status(409).json({ error: 'User already exists' });
    }
    console.log('✅ Email is available');

    // Hash password
    console.log('🔐 Starting password hashing...');
    const saltRounds = 12;
    const passwordHash = await bcrypt.hash(password, saltRounds);
    console.log('✅ Password hashed successfully');

    // Create user
    console.log('👤 Creating new user in database...');
    const result = await db.query(`
      INSERT INTO users (email, password_hash, company_name, first_name, last_name)
      VALUES ($1, $2, $3, $4, $5)
      RETURNING id, email, company_name, first_name, last_name, created_at
    `, [email, passwordHash, company_name, first_name, last_name]);
    
    console.log('📊 Database insert result rows:', result.rows.length);
    if (result.rows.length === 0) {
      throw new Error('Failed to create user - no rows returned');
    }

    const user = result.rows[0];
    console.log('✅ User created successfully:', {
      id: user.id,
      email: user.email,
      company_name: user.company_name,
      first_name: user.first_name,
      last_name: user.last_name
    });

    // Generate tokens
    console.log('🎫 Generating authentication tokens...');
    const tokens = generateTokens(user.id, user.email);
    console.log('✅ Tokens generated successfully');

    console.log('🎉 Registration completed successfully for user:', user.email);
    
    res.status(201).json({
      user: {
        id: user.id,
        email: user.email,
        company_name: user.company_name,
        first_name: user.first_name,
        last_name: user.last_name
      },
      ...tokens
    });
    
    console.log('=== REGISTRATION ENDPOINT FINISHED SUCCESSFULLY ===');

  } catch (dbError) {
    console.error('❌ DATABASE/PROCESSING ERROR in registration:');
    console.error('❌ Error message:', dbError.message);
    console.error('❌ Error stack:', dbError.stack);
    console.error('❌ Error code:', dbError.code);
    console.error('❌ Error detail:', dbError.detail);
    
    // Log specific database error info if available
    if (dbError.code) {
      console.error('❌ PostgreSQL Error Code:', dbError.code);
    }
    
    return res.status(500).json({
      error: 'Internal server error during registration',
      message: process.env.NODE_ENV === 'development' ? dbError.message : 'Registration failed'
    });
  }
}));
/**
 * @swagger
 * /api/auth/login:
 *   post:
 *     summary: Login user
 *     tags: [Authentication]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/LoginRequest'
 *     responses:
 *       200:
 *         description: Login successful
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/AuthResponse'
 *       400:
 *         description: Validation failed
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       401:
 *         description: Invalid credentials
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
// Login
router.post('/login', validateLogin, asyncHandler(async (req, res) => {
  console.log('=== LOGIN ENDPOINT STARTED ===');
  console.log('📝 Received request body:', {
    email: req.body.email,
    password: req.body.password ? '***provided***' : 'missing'
  });
  console.log('📋 Headers:', req.headers);
  
  // Check validation results
  console.log('🔍 Checking validation results...');
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    console.error('❌ VALIDATION FAILED:', errors.array());
    return res.status(400).json({ 
      error: 'Validation failed',
      details: errors.array()
    });
  }
  console.log('✅ Validation passed');

  // Sanitize data
  console.log('🧹 Sanitizing request data...');
  const { email, password } = sanitizeObject(req.body);
  console.log('✅ Data sanitized for email:', email);

  try {
    // Get user
    console.log('🔍 Searching for user with email:', email);
    const result = await db.query(`
      SELECT id, email, password_hash, company_name, first_name, last_name
      FROM users WHERE email = $1
    `, [email]);
    
    console.log('📊 Database query result - users found:', result.rows.length);

    if (result.rows.length === 0) {
      console.log('❌ No user found with email:', email);
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const user = result.rows[0];
    console.log('✅ User found:', {
      id: user.id,
      email: user.email,
      company_name: user.company_name,
      first_name: user.first_name,
      last_name: user.last_name
    });

    // Verify password
    console.log('🔐 Verifying password...');
    const isValidPassword = await bcrypt.compare(password, user.password_hash);
    console.log('🔐 Password verification result:', isValidPassword ? 'VALID' : 'INVALID');
    
    if (!isValidPassword) {
      console.log('❌ Invalid password for user:', email);
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    console.log('✅ Password verified successfully');

    // Generate tokens
    console.log('🎫 Generating authentication tokens...');
    const tokens = generateTokens(user.id, user.email);
    console.log('✅ Tokens generated successfully');

    console.log('🎉 Login completed successfully for user:', user.email);

    res.json({
      user: {
        id: user.id,
        email: user.email,
        company_name: user.company_name,
        first_name: user.first_name,
        last_name: user.last_name
      },
      ...tokens
    });

    console.log('=== LOGIN ENDPOINT FINISHED SUCCESSFULLY ===');

  } catch (dbError) {
    console.error('❌ DATABASE/PROCESSING ERROR in login:');
    console.error('❌ Error message:', dbError.message);
    console.error('❌ Error stack:', dbError.stack);
    console.error('❌ Error code:', dbError.code);
    console.error('❌ Error detail:', dbError.detail);
    
    // Log specific database error info if available
    if (dbError.code) {
      console.error('❌ PostgreSQL Error Code:', dbError.code);
    }
    
    return res.status(500).json({
      error: 'Internal server error during login',
      message: process.env.NODE_ENV === 'development' ? dbError.message : 'Login failed'
    });
  }
}));

/**
 * @swagger
 * /api/auth/logout:
 *   post:
 *     summary: Logout user
 *     tags: [Authentication]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Logout successful
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                   example: Logged out successfully
 */
// Logout
router.post('/logout', authenticateToken, (req, res) => {
  const token = req.headers['authorization']?.split(' ')[1];
  if (token) {
    revokeToken(token);
  }
  res.json({ message: 'Logged out successfully' });
});

/**
 * @swagger
 * /api/auth/me:
 *   get:
 *     summary: Get current user information
 *     tags: [Authentication]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: User information retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/User'
 *       401:
 *         description: Unauthorized - Invalid or missing token
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       404:
 *         description: User not found
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
// Get current user
router.get('/me', authenticateToken, asyncHandler(async (req, res) => {
  const result = await db.query(`
    SELECT id, email, company_name, first_name, last_name, created_at
    FROM users WHERE id = $1
  `, [req.user.id]);

  if (result.rows.length === 0) {
    return res.status(404).json({ error: 'User not found' });
  }

  res.json(result.rows[0]);
}));

module.exports = router;