// src/models/Question.js
const pool = require('../config/database');

class Question {
  static async createBatch(productId, questions) {
    const client = await pool.connect();
    
    try {
      await client.query('BEGIN');
      
      const insertPromises = questions.map((question, index) => {
        const query = `
          INSERT INTO questions (product_id, question_text, question_type, question_order, ai_generated, created_at)
          VALUES ($1, $2, $3, $4, $5, NOW())
          RETURNING *
        `;
        return client.query(query, [
          productId,
          question.text,
          question.type || 'text',
          question.order || index + 1,
          question.ai_generated !== false
        ]);
      });
      
      const results = await Promise.all(insertPromises);
      await client.query('COMMIT');
      
      return results.map(result => result.rows[0]);
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }

  static async findByProduct(productId) {
    const query = `
      SELECT * FROM questions 
      WHERE product_id = $1 
      ORDER BY question_order ASC
    `;
    const result = await pool.query(query, [productId]);
    return result.rows;
  }
}

module.exports = Question;