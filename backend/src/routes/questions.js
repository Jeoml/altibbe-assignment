const express = require('express');
const Question = require('../models/Question');
const Answer = require('../models/Answer');
const Product = require('../models/Product');
const { authenticateToken } = require('../middleware/auth');
const { aiService } = require('../services/aiService');

const router = express.Router();

// Get questions for a product
router.get('/product/:productId', authenticateToken, async (req, res) => {
  try {
    const { productId } = req.params;
    
    // Verify product ownership
    const product = await Product.findById(productId);
    if (!product || product.user_id !== req.user.id) {
      return res.status(404).json({ error: 'Product not found' });
    }

    const questions = await Question.findByProduct(productId);
    res.json(questions);
  } catch (error) {
    console.error('Get questions error:', error);
    res.status(500).json({ error: 'Failed to fetch questions' });
  }
});

// Submit answers
router.post('/product/:productId/answers', authenticateToken, async (req, res) => {
  try {
    const { productId } = req.params;
    const { answers } = req.body;

    // Verify product ownership
    const product = await Product.findById(productId);
    if (!product || product.user_id !== req.user.id) {
      return res.status(404).json({ error: 'Product not found' });
    }

    // Validate answers format
    if (!Array.isArray(answers) || answers.length === 0) {
      return res.status(400).json({ error: 'Invalid answers format' });
    }

    const savedAnswers = await Answer.createBatch(answers);
    res.json(savedAnswers);
  } catch (error) {
    console.error('Submit answers error:', error);
    res.status(500).json({ error: 'Failed to submit answers' });
  }
});

// Regenerate questions (call AI service)
router.post('/product/:productId/regenerate', authenticateToken, async (req, res) => {
  try {
    const { productId } = req.params;
    
    const product = await Product.findById(productId);
    if (!product || product.user_id !== req.user.id) {
      return res.status(404).json({ error: 'Product not found' });
    }

    const questions = await aiService.generateQuestions(productId, {
      name: product.name,
      category: product.category,
      description: product.description
    });

    res.json(questions);
  } catch (error) {
    console.error('Regenerate questions error:', error);
    res.status(500).json({ error: 'Failed to regenerate questions' });
  }
});

module.exports = router;