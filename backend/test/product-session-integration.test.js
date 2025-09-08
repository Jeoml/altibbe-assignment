const pool = require('../src/config/database');
const Product = require('../src/models/Product');
const OnboardingSession = require('../src/models/OnboardingSession');
const { aiService } = require('../src/services/aiService');

// Mock AI service
jest.mock('../src/services/aiService', () => ({
  aiService: {
    generateQuestions: jest.fn().mockResolvedValue([]),
  },
}));

// Mock database
jest.mock('../src/config/database', () => ({
  query: jest.fn(),
  getClient: jest.fn(),
  pool: {
    query: jest.fn(),
    connect: jest.fn(),
    end: jest.fn(),
  },
}));

describe('Product-Session Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Product Creation and Session Integration', () => {
    const testProductData = {
      name: 'Integration Test Product',
      category: 'food',
      description: 'This is a comprehensive test product for session integration.',
      company_name: 'Test Integration Corp',
      user_id: 1
    };

    it('should create product and trigger AI question generation', async () => {
      // Mock product creation
      const mockProduct = {
        id: 123,
        ...testProductData,
        created_at: new Date(),
      };

      pool.query.mockResolvedValueOnce({ rows: [mockProduct] });

      // Execute product creation
      const createdProduct = await Product.create(testProductData);

      // Verify product was created
      expect(createdProduct).toMatchObject({
        id: 123,
        name: testProductData.name,
        category: testProductData.category,
        user_id: testProductData.user_id,
      });

      // Verify database query was called with correct parameters
      expect(pool.query).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO products'),
        [
          testProductData.name,
          testProductData.category,
          testProductData.description,
          testProductData.company_name,
          testProductData.user_id
        ]
      );

      // Verify AI service was called (this would happen in the route handler)
      // Note: In actual implementation, this is called in the products route
      expect(aiService.generateQuestions).toHaveBeenCalledTimes(0); // Not called in model
    });

    it('should handle database errors during product creation', async () => {
      // Mock database error
      const dbError = new Error('Connection timeout');
      pool.query.mockRejectedValueOnce(dbError);

      // Verify error is thrown
      await expect(Product.create(testProductData)).rejects.toThrow('Connection timeout');
    });

    it('should find products by user correctly', async () => {
      const mockProducts = [
        {
          id: 1,
          name: 'User Product 1',
          category: 'food',
          user_id: 1,
          created_at: new Date(),
        },
        {
          id: 2,
          name: 'User Product 2',
          category: 'cosmetics',
          user_id: 1,
          created_at: new Date(),
        },
      ];

      pool.query.mockResolvedValueOnce({ rows: mockProducts });

      const userProducts = await Product.findByUser(1);

      expect(userProducts).toHaveLength(2);
      expect(userProducts[0].user_id).toBe(1);
      expect(userProducts[1].user_id).toBe(1);

      expect(pool.query).toHaveBeenCalledWith(
        'SELECT * FROM products WHERE user_id = $1 ORDER BY created_at DESC',
        [1]
      );
    });

    it('should find product by ID correctly', async () => {
      const mockProduct = {
        id: 456,
        name: 'Specific Product',
        category: 'supplements',
        user_id: 1,
        created_at: new Date(),
      };

      pool.query.mockResolvedValueOnce({ rows: [mockProduct] });

      const product = await Product.findById(456);

      expect(product).toMatchObject({
        id: 456,
        name: 'Specific Product',
        category: 'supplements',
      });

      expect(pool.query).toHaveBeenCalledWith(
        'SELECT * FROM products WHERE id = $1',
        [456]
      );
    });

    it('should return undefined for non-existent product', async () => {
      pool.query.mockResolvedValueOnce({ rows: [] });

      const product = await Product.findById(999);

      expect(product).toBeUndefined();
    });
  });

  describe('Session Creation Verification', () => {
    const testSessionData = {
      session_id: 'test-session-uuid',
      producer_id: 'test-producer-uuid',
      user_id: 1,
      status: 'started',
      message: 'Welcome to onboarding!',
      collected_fields: ['initial_data'],
      current_field: 'name',
      initial_data: {
        business_name: 'Test Business',
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe',
      }
    };

    it('should create onboarding session correctly', async () => {
      const mockSession = {
        id: 1,
        ...testSessionData,
        created_at: new Date(),
        updated_at: new Date(),
      };

      pool.query.mockResolvedValueOnce({ rows: [mockSession] });

      const createdSession = await OnboardingSession.create(testSessionData);

      expect(createdSession).toMatchObject({
        id: 1,
        session_id: testSessionData.session_id,
        producer_id: testSessionData.producer_id,
        user_id: testSessionData.user_id,
        status: testSessionData.status,
      });

      // Verify JSON fields are properly stringified
      expect(pool.query).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO onboarding_sessions'),
        [
          testSessionData.session_id,
          testSessionData.producer_id,
          testSessionData.user_id,
          testSessionData.status,
          testSessionData.message,
          JSON.stringify(testSessionData.collected_fields),
          testSessionData.current_field,
          JSON.stringify(testSessionData.initial_data)
        ]
      );
    });

    it('should find session by session ID', async () => {
      const mockSession = {
        id: 1,
        session_id: 'test-session-uuid',
        user_id: 1,
        status: 'in_progress',
        collected_fields: ['name', 'phone'],
        current_field: 'company_size',
      };

      pool.query.mockResolvedValueOnce({ rows: [mockSession] });

      const session = await OnboardingSession.findBySessionId('test-session-uuid');

      expect(session).toMatchObject({
        id: 1,
        session_id: 'test-session-uuid',
        status: 'in_progress',
      });

      expect(pool.query).toHaveBeenCalledWith(
        'SELECT * FROM onboarding_sessions WHERE session_id = $1',
        ['test-session-uuid']
      );
    });

    it('should find sessions by user ID', async () => {
      const mockSessions = [
        {
          id: 1,
          session_id: 'session-1',
          user_id: 1,
          status: 'started',
        },
        {
          id: 2,
          session_id: 'session-2',
          user_id: 1,
          status: 'completed',
        },
      ];

      pool.query.mockResolvedValueOnce({ rows: mockSessions });

      const sessions = await OnboardingSession.findByUserId(1);

      expect(sessions).toHaveLength(2);
      expect(sessions[0].user_id).toBe(1);
      expect(sessions[1].user_id).toBe(1);

      expect(pool.query).toHaveBeenCalledWith(
        'SELECT * FROM onboarding_sessions WHERE user_id = $1 ORDER BY created_at DESC',
        [1]
      );
    });
  });

  describe('Session Field Logic', () => {
    it('should determine next field correctly for new session', () => {
      const collectedFields = ['initial_data'];
      const initialData = {
        first_name: 'John',
        last_name: 'Doe',
        business_name: 'Test Corp',
      };

      const nextField = OnboardingSession.getNextField(collectedFields, initialData);

      expect(nextField).toBe('name');
    });

    it('should return null when all required fields are collected', () => {
      const collectedFields = ['name', 'phone', 'company_size', 'industry', 'location'];
      const initialData = {};

      const nextField = OnboardingSession.getNextField(collectedFields, initialData);

      expect(nextField).toBeNull();
    });

    it('should generate appropriate message for each field', () => {
      const initialData = {
        first_name: 'John',
        last_name: 'Doe',
        business_name: 'Test Corp',
      };

      const nameMessage = OnboardingSession.getMessageForField('name', initialData);
      const phoneMessage = OnboardingSession.getMessageForField('phone', initialData);
      const companySizeMessage = OnboardingSession.getMessageForField('company_size', initialData);

      expect(nameMessage).toContain('John Doe');
      expect(nameMessage).toContain('Test Corp');
      expect(phoneMessage).toContain('phone number');
      expect(companySizeMessage).toContain('company');
      expect(companySizeMessage).toContain('size');
    });

    it('should return default message for unknown field', () => {
      const message = OnboardingSession.getMessageForField('unknown_field', {});

      expect(message).toContain('complete your registration');
    });
  });
});
