// src/models/Answer.js
const pool = require('../config/database');

class Answer {
  static async createBatch(answers) {
    const client = await pool.connect();
    
    try {
      await client.query('BEGIN');
      
      const insertPromises = answers.map(answer => {
        const query = `
          INSERT INTO answers (question_id, answer_text, created_at)
          VALUES ($1, $2, NOW())
          RETURNING *
        `;
        return client.query(query, [answer.question_id, answer.answer_text]);
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
      SELECT a.*, q.question_text, q.question_type
      FROM answers a
      JOIN questions q ON a.question_id = q.id
      WHERE q.product_id = $1
      ORDER BY q.question_order ASC
    `;
    const result = await pool.query(query, [productId]);
    return result.rows;
  }
}

module.exports = Answer;