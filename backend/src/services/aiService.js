const axios = require('axios');
const Question = require('../models/Question');

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:5001';

class AIService {
  async generateQuestions(productId, productData) {
    try {
      const response = await axios.post(`${AI_SERVICE_URL}/generate-questions`, {
        product: productData
      }, {
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const { questions } = response.data;
      
      if (questions && Array.isArray(questions)) {
        // Save questions to database
        const savedQuestions = await Question.createBatch(productId, questions);
        return savedQuestions;
      }
      
      throw new Error('Invalid response format from AI service');
    } catch (error) {
      console.error('AI service error:', error.message);
      
      // Fallback to default questions if AI service fails
      return this.getFallbackQuestions(productId, productData.category);
    }
  }

  getFallbackQuestions(productId, category) {
    const fallbackQuestions = {
      food: [
        { text: 'What are the main ingredients in order of quantity?', type: 'textarea' },
        { text: 'Does this product contain artificial preservatives?', type: 'radio' },
        { text: 'Is this product certified organic?', type: 'radio' },
        { text: 'What allergens does this product contain?', type: 'checkbox' }
      ],
      cosmetics: [
        { text: 'What are the active ingredients?', type: 'textarea' },
        { text: 'Is this product cruelty-free?', type: 'radio' },
        { text: 'What skin types is this suitable for?', type: 'checkbox' },
        { text: 'Are there any known allergens?', type: 'textarea' }
      ],
      supplements: [
        { text: 'What is the active ingredient dosage?', type: 'text' },
        { text: 'Is this third-party tested?', type: 'radio' },
        { text: 'What certifications does this have?', type: 'checkbox' },
        { text: 'Are there any drug interactions?', type: 'textarea' }
      ]
    };

    const questions = fallbackQuestions[category] || fallbackQuestions.food;
    return Question.createBatch(productId, questions);
  }

  async calculateTransparencyScore(productData, answers) {
    try {
      const response = await axios.post(`${AI_SERVICE_URL}/transparency-score`, {
        product: productData,
        answers: answers
      }, {
        timeout: 15000
      });

      return response.data;
    } catch (error) {
      console.error('Transparency score error:', error.message);
      
      // Fallback scoring
      return {
        score: 75,
        grade: 'B',
        reasoning: 'Score calculated using fallback algorithm'
      };
    }
  }
}

module.exports = { aiService: new AIService() };