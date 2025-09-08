// src/routes/onboarding.js
const express = require('express');
const { body, validationResult } = require('express-validator');
const { v4: uuidv4 } = require('uuid');
const { authenticateToken } = require('../middleware/auth');
const { asyncHandler } = require('../middleware/errorHandler');
const { sanitizeObject } = require('../middleware/security');
const OnboardingSession = require('../models/OnboardingSession');

const router = express.Router();

/**
 * @swagger
 * components:
 *   schemas:
 *     InitialData:
 *       type: object
 *       required:
 *         - business_name
 *         - email
 *         - first_name
 *         - last_name
 *       properties:
 *         business_name:
 *           type: string
 *           description: Business/company name
 *         email:
 *           type: string
 *           format: email
 *           description: Contact email
 *         first_name:
 *           type: string
 *           description: First name
 *         last_name:
 *           type: string
 *           description: Last name
 *     OnboardingStartRequest:
 *       type: object
 *       required:
 *         - initial_data
 *       properties:
 *         initial_data:
 *           $ref: '#/components/schemas/InitialData'
 *     OnboardingStartResponse:
 *       type: object
 *       properties:
 *         session_id:
 *           type: string
 *           format: uuid
 *           description: Unique session identifier
 *         producer_id:
 *           type: string
 *           format: uuid
 *           description: Producer identifier
 *         status:
 *           type: string
 *           enum: [started, in_progress, completed]
 *           description: Current onboarding status
 *         message:
 *           type: string
 *           description: Message to display to user
 *         collected_fields:
 *           type: array
 *           items:
 *             type: string
 *           description: List of fields already collected
 *         current_field:
 *           type: string
 *           description: Next field to collect from user
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

// Validation for initial_data object
const validateInitialData = [
  body('initial_data')
    .isObject()
    .withMessage('initial_data must be an object'),

  body('initial_data.business_name')
    .trim()
    .isLength({ min: 1, max: 255 })
    .withMessage('Business name is required and must be 1-255 characters'),

  body('initial_data.email')
    .isEmail()
    .normalizeEmail()
    .withMessage('Valid email is required'),

  body('initial_data.first_name')
    .trim()
    .isLength({ min: 1, max: 100 })
    .withMessage('First name is required and must be 1-100 characters'),

  body('initial_data.last_name')
    .trim()
    .isLength({ min: 1, max: 100 })
    .withMessage('Last name is required and must be 1-100 characters')
];

/**
 * @swagger
 * /api/onboarding/start:
 *   post:
 *     summary: Start a new onboarding session
 *     tags: [Onboarding]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/OnboardingStartRequest'
 *     responses:
 *       200:
 *         description: Onboarding session started successfully
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/OnboardingStartResponse'
 *       400:
 *         description: Validation failed
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       401:
 *         description: Unauthorized - Invalid or missing token
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       422:
 *         description: Invalid input data
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.post('/start', authenticateToken, validateInitialData, asyncHandler(async (req, res) => {
  console.log('=== ONBOARDING START ENDPOINT STARTED ===');
  console.log('📝 Received request body:', req.body);
  console.log('👤 User ID from token:', req.user.id);

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
  const { initial_data } = sanitizedData;
  console.log('✅ Data sanitized');

  try {
    // Generate unique IDs
    const sessionId = uuidv4();
    const producerId = uuidv4();
    console.log('🎯 Generated IDs:', { sessionId, producerId });

    // Determine collected fields and next field
    const collectedFields = ['initial_data'];
    const currentField = OnboardingSession.getNextField(collectedFields, initial_data);
    console.log('📋 Field determination:', { collectedFields, currentField });

    // Generate appropriate message
    const message = OnboardingSession.getMessageForField(currentField, initial_data);
    console.log('💬 Generated message:', message);

    // Create onboarding session
    console.log('💾 Creating onboarding session in database...');
    const sessionData = {
      session_id: sessionId,
      producer_id: producerId,
      user_id: req.user.id,
      status: 'started',
      message,
      collected_fields: collectedFields,
      current_field: currentField,
      initial_data
    };

    const session = await OnboardingSession.create(sessionData);
    console.log('✅ Onboarding session created successfully');

    // Prepare response
    const response = {
      session_id: session.session_id,
      producer_id: session.producer_id,
      status: session.status,
      message: session.message,
      collected_fields: JSON.parse(session.collected_fields),
      current_field: session.current_field
    };

    console.log('🎉 Onboarding session started successfully for user:', req.user.id);
    console.log('=== ONBOARDING START ENDPOINT FINISHED SUCCESSFULLY ===');

    res.status(200).json(response);

  } catch (dbError) {
    console.error('❌ DATABASE ERROR in onboarding start:');
    console.error('❌ Error message:', dbError.message);
    console.error('❌ Error stack:', dbError.stack);
    console.error('❌ Error code:', dbError.code);
    console.error('❌ Error detail:', dbError.detail);

    // Handle specific database errors
    if (dbError.code === '23505') { // Unique violation
      return res.status(409).json({
        error: 'Session already exists',
        message: 'An onboarding session is already in progress'
      });
    }

    return res.status(500).json({
      error: 'Internal server error during onboarding',
      message: process.env.NODE_ENV === 'development' ? dbError.message : 'Failed to start onboarding'
    });
  }
}));

/**
 * @swagger
 * /api/onboarding/{session_id}:
 *   get:
 *     summary: Get onboarding session status
 *     tags: [Onboarding]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: session_id
 *         required: true
 *         schema:
 *           type: string
 *           format: uuid
 *         description: Session ID
 *     responses:
 *       200:
 *         description: Session retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/OnboardingStartResponse'
 *       401:
 *         description: Unauthorized
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       404:
 *         description: Session not found
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.get('/:session_id', authenticateToken, asyncHandler(async (req, res) => {
  const { session_id } = req.params;

  console.log('🔍 Getting onboarding session:', session_id);

  const session = await OnboardingSession.findBySessionId(session_id);

  if (!session) {
    return res.status(404).json({ error: 'Session not found' });
  }

  // Check if session belongs to authenticated user
  if (session.user_id !== req.user.id) {
    return res.status(403).json({ error: 'Access denied to this session' });
  }

  const response = {
    session_id: session.session_id,
    producer_id: session.producer_id,
    status: session.status,
    message: session.message,
    collected_fields: JSON.parse(session.collected_fields),
    current_field: session.current_field
  };

  res.json(response);
}));

module.exports = router;
