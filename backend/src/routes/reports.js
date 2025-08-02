const express = require('express');
const axios = require('axios');
const { authenticateToken } = require('../middleware/auth');
const { asyncHandler } = require('../middleware/errorHandler');

const router = express.Router();

/**
 * @swagger
 * /api/reports/{productId}:
 *   get:
 *     summary: Generate transparency report for product
 *     tags: [Reports]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: productId
 *         required: true
 *         schema:
 *           type: integer
 *       - in: header
 *         name: x-session-id
 *         required: true
 *         schema:
 *           type: string
 *         description: Session ID for AI service
 *     responses:
 *       200:
 *         description: Report generated successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 reportId:
 *                   type: string
 *                   example: "report_123_1672531200000"
 *                 productId:
 *                   type: integer
 *                   example: 123
 *                 sessionId:
 *                   type: string
 *                   example: "session_abc123xyz"
 *                 status:
 *                   type: string
 *                   enum: [completed, processing, failed]
 *                   example: "completed"
 *                 message:
 *                   type: string
 *                   example: "Report generated successfully"
 *                 userId:
 *                   type: integer
 *                   example: 456
 *                 aiResponse:
 *                   type: object
 *                   description: Response from AI service
 *       400:
 *         description: Missing session ID
 *       401:
 *         description: Unauthorized
 *       404:
 *         description: Product not found
 *       408:
 *         description: Request timeout
 *       503:
 *         description: AI service unavailable
 */
router.get('/:productId', authenticateToken, asyncHandler(async (req, res) => {
  const { productId } = req.params;
  const sessionId = req.headers['x-session-id'];
  const bearerToken = req.headers.authorization;

  // Validate session ID
  if (!sessionId) {
    return res.status(400).json({ 
      error: 'Session ID is required',
      message: 'Please provide x-session-id header'
    });
  }

  // Bearer token is automatically validated by authenticateToken middleware
  // Extract it for AI service if needed

  try {
    // Check if AI service is configured
    const aiServiceUrl = process.env.AI_SERVICE_URL;
    if (!aiServiceUrl) {
      return res.status(503).json({
        error: 'AI service not configured',
        message: 'AI_SERVICE_URL environment variable is not set'
      });
    }

    // For now, let's mock the AI service response since the external service may not be running
    // or may require different authentication
    
    // Uncomment this section when you have a working AI service:
    /*
    const aiResponse = await axios.post(`${aiServiceUrl}/chat`, {
      productId: parseInt(productId),
      userId: req.user.id,
      sessionId: sessionId,
      message: `Generate a transparency report for product ID ${productId}`
    }, {
      headers: {
        'Content-Type': 'application/json',
        'x-session-id': sessionId
        // Note: Remove Authorization header as AI service may not expect JWT tokens
      },
      timeout: 30000 // 30 second timeout
    });
    */

    // Mock AI service response for now
    const mockAiResponse = {
      reportId: `report_${productId}_${Date.now()}`,
      transparencyScore: 85,
      findings: [
        "Product sourcing information is well documented",
        "Manufacturing process transparency is good", 
        "Supply chain visibility could be improved"
      ],
      recommendations: [
        "Add more supplier verification details",
        "Include carbon footprint calculations",
        "Provide third-party certification status"
      ],
      generatedAt: new Date().toISOString()
    };

    res.json({ 
      reportId: `report_${productId}_${Date.now()}`,
      productId: parseInt(productId),
      sessionId: sessionId,
      status: 'completed',
      message: 'Report generated successfully (mock data)',
      userId: req.user.id,
      aiResponse: mockAiResponse
    });

    res.json({ 
      reportId: `report_${productId}_${Date.now()}`,
      productId: parseInt(productId),
      sessionId: sessionId,
      status: 'completed',
      message: 'Report generated successfully (mock data)',
      userId: req.user.id,
      aiResponse: mockAiResponse
    });
  } catch (error) {
    console.error('AI service error:', error);
    
    // Handle different types of errors
    if (error.code === 'ECONNREFUSED') {
      return res.status(503).json({
        error: 'AI service unavailable',
        message: 'Could not connect to AI service'
      });
    }
    
    if (error.response) {
      // AI service returned an error response
      return res.status(error.response.status).json({
        error: 'AI service error',
        message: error.response.data?.message || 'AI service request failed',
        details: error.response.data
      });
    }
    
    if (error.code === 'ECONNABORTED') {
      return res.status(408).json({
        error: 'Request timeout',
        message: 'AI service took too long to respond'
      });
    }
    
    res.status(500).json({
      error: 'Failed to generate report',
      message: 'Internal server error'
    });
  }
}));

module.exports = router;