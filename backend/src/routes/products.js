// src/routes/products.js
const express = require('express');
const { body, param, validationResult } = require('express-validator');
const Product = require('../models/Product');
const { authenticateToken } = require('../middleware/auth');
const { aiService } = require('../services/aiService');

const router = express.Router();

// Validation middleware
const validateProduct = [
  body('name').trim().isLength({ min: 1, max: 255 }).withMessage('Product name is required'),
  body('category').trim().isIn(['food', 'cosmetics', 'supplements', 'household', 'other']).withMessage('Invalid category'),
  body('description').trim().isLength({ min: 10, max: 2000 }).withMessage('Description must be 10-2000 characters'),
  body('company_name').trim().isLength({ min: 1, max: 255 }).withMessage('Company name is required')
];

// Create product
router.post('/', authenticateToken, validateProduct, async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const productData = {
      ...req.body,
      user_id: req.user.id
    };

    const product = await Product.create(productData);
    
    // Trigger AI question generation
    try {
      await aiService.generateQuestions(product.id, {
        name: product.name,
        category: product.category,
        description: product.description
      });
    } catch (aiError) {
      console.error('AI service error:', aiError);
      // Continue even if AI fails
    }

    res.status(201).json(product);
  } catch (error) {
    console.error('Create product error:', error);
    res.status(500).json({ error: 'Failed to create product' });
  }
});

// Get user's products
router.get('/', authenticateToken, async (req, res) => {
  try {
    const products = await Product.findByUser(req.user.id);
    res.json(products);
  } catch (error) {
    console.error('Get products error:', error);
    res.status(500).json({ error: 'Failed to fetch products' });
  }
});

// Get single product
router.get('/:id', authenticateToken, async (req, res) => {
  try {
    const product = await Product.findById(req.params.id);
    
    if (!product) {
      return res.status(404).json({ error: 'Product not found' });
    }

    // Check ownership
    if (product.user_id !== req.user.id) {
      return res.status(403).json({ error: 'Access denied' });
    }

    res.json(product);
  } catch (error) {
    console.error('Get product error:', error);
    res.status(500).json({ error: 'Failed to fetch product' });
  }
});

module.exports = router;
