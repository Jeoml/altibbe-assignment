const pool = require('../config/database');
const { v4: uuidv4 } = require('uuid');

class OnboardingSession {
  static async create(sessionData) {
    const {
      session_id,
      producer_id,
      user_id,
      status,
      message,
      collected_fields,
      current_field,
      initial_data
    } = sessionData;

    const query = `
      INSERT INTO onboarding_sessions (
        session_id,
        producer_id,
        user_id,
        status,
        message,
        collected_fields,
        current_field,
        initial_data,
        created_at
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
      RETURNING *
    `;

    const values = [
      session_id,
      producer_id,
      user_id,
      status,
      message,
      JSON.stringify(collected_fields),
      current_field,
      JSON.stringify(initial_data)
    ];

    const result = await pool.query(query, values);
    return result.rows[0];
  }

  static async findBySessionId(session_id) {
    const query = 'SELECT * FROM onboarding_sessions WHERE session_id = $1';
    const result = await pool.query(query, [session_id]);
    return result.rows[0];
  }

  static async findByUserId(user_id) {
    const query = 'SELECT * FROM onboarding_sessions WHERE user_id = $1 ORDER BY created_at DESC';
    const result = await pool.query(query, [user_id]);
    return result.rows;
  }

  static async update(session_id, updateData) {
    const fields = Object.keys(updateData);
    const values = Object.values(updateData);
    const setClause = fields.map((field, index) => `${field} = $${index + 2}`).join(', ');

    const query = `
      UPDATE onboarding_sessions
      SET ${setClause}, updated_at = NOW()
      WHERE session_id = $1
      RETURNING *
    `;

    const result = await pool.query(query, [session_id, ...values]);
    return result.rows[0];
  }

  static async delete(session_id) {
    const query = 'DELETE FROM onboarding_sessions WHERE session_id = $1 RETURNING *';
    const result = await pool.query(query, [session_id]);
    return result.rows[0];
  }

  // Helper method to determine the next field to collect
  static getNextField(collectedFields, initialData) {
    const requiredFields = ['name', 'phone', 'company_size', 'industry', 'location'];
    const missingFields = requiredFields.filter(field => !collectedFields.includes(field));

    // If we have initial data with name, mark name as collected
    if (initialData && initialData.first_name && initialData.last_name && !collectedFields.includes('name')) {
      return 'name'; // Name is already provided, but we might want to confirm it
    }

    return missingFields.length > 0 ? missingFields[0] : null;
  }

  // Helper method to generate onboarding message based on current field
  static getMessageForField(currentField, initialData) {
    const messages = {
      name: `Great! I see you're ${initialData.first_name} ${initialData.last_name} from ${initialData.business_name}. To complete your registration, could you please confirm your full name?`,
      phone: "Thank you! Now, could you please provide your phone number for verification?",
      company_size: "Great! What is the size of your company? (e.g., 1-10, 11-50, 51-200, 200+)",
      industry: "Excellent! What industry is your company in?",
      location: "Perfect! Finally, could you please tell us your business location?"
    };

    return messages[currentField] || "To complete your registration, I just need to confirm a few more details.";
  }
}

module.exports = OnboardingSession;


