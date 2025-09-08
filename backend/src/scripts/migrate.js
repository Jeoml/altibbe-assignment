// src/scripts/migrate.js
const pool = require('../config/database');

const createTables = async () => {
  try {
    // Users table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        company_name VARCHAR(255),
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      )
    `);

    // Products table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        category VARCHAR(100) NOT NULL,
        description TEXT,
        company_name VARCHAR(255),
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      )
    `);

    // Questions table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS questions (
        id SERIAL PRIMARY KEY,
        product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
        question_text TEXT NOT NULL,
        question_type VARCHAR(50) DEFAULT 'text',
        question_order INTEGER DEFAULT 1,
        ai_generated BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT NOW()
      )
    `);

    // Answers table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS answers (
        id SERIAL PRIMARY KEY,
        question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
        answer_text TEXT,
        created_at TIMESTAMP DEFAULT NOW()
      )
    `);

    // Reports table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS reports (
        id SERIAL PRIMARY KEY,
        product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
        pdf_url VARCHAR(500),
        transparency_score INTEGER,
        score_reasoning TEXT,
        generated_at TIMESTAMP DEFAULT NOW()
      )
    `);

    // Onboarding Sessions table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS onboarding_sessions (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR(36) UNIQUE NOT NULL,
        producer_id VARCHAR(36) UNIQUE NOT NULL,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        status VARCHAR(50) DEFAULT 'started',
        message TEXT,
        collected_fields JSONB DEFAULT '[]',
        current_field VARCHAR(100),
        initial_data JSONB,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      )
    `);

    console.log('✅ Database tables created successfully');
  } catch (error) {
    console.error('❌ Migration error:', error);
  } finally {
    // Close the database connection pool
    if (pool && typeof pool.end === 'function') {
      await pool.end();
    }
  }
};

// Run migration
if (require.main === module) {
  createTables().then(() => {
    process.exit(0);
  }).catch((error) => {
    console.error('Migration failed:', error);
    process.exit(1);
  });
}

module.exports = { createTables };