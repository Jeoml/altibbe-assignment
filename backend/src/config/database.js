// src/config/database.js
const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { 
    rejectUnauthorized: false,
    sslmode: 'require'
  },
  max: 10, // Reduced for NeonDB
  min: 0,
  acquireTimeoutMillis: 60000,
  createTimeoutMillis: 30000,
  destroyTimeoutMillis: 5000,
  idleTimeoutMillis: 30000,
  reapIntervalMillis: 1000,
  createRetryIntervalMillis: 200,
});

// Test connection with retry
const testConnection = async (retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      console.log(`🔍 Database connection attempt ${i + 1}/${retries}`);
      const client = await pool.connect();
      await client.query('SELECT NOW()');
      console.log('✅ Database connected successfully');
      client.release();
      return true;
    } catch (err) {
      console.error(`❌ Attempt ${i + 1} failed:`, err.message);
      if (i < retries - 1) {
        console.log('⏳ Retrying in 2 seconds...');
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
  }
  console.log('⚠️ All connection attempts failed, starting server anyway');
  return false;
};

// Initialize with retry
testConnection();

module.exports = {
  query: (text, params) => pool.query(text, params),
  getClient: () => pool.connect(),
  pool
};