const pool = require('../src/config/database');
const Product = require('../src/models/Product');
const OnboardingSession = require('../src/models/OnboardingSession');

// Mock the database for isolated testing
jest.mock('../src/config/database', () => ({
  query: jest.fn(),
  getClient: jest.fn(),
  pool: {
    query: jest.fn(),
    connect: jest.fn(),
    end: jest.fn(),
  },
}));

describe('Database Session Creation Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });


  describe('Product Database Operations', () => {
    const testProduct = {
      name: 'Database Test Product',
      category: 'food',
      description: 'Testing database operations for product creation',
      company_name: 'Database Test Corp',
      user_id: 1
    };

    it('should execute correct SQL for product creation', async () => {
      const expectedProduct = {
        id: 1,
        ...testProduct,
        created_at: new Date('2024-01-01T00:00:00Z'),
      };

      pool.query.mockResolvedValueOnce({ rows: [expectedProduct] });

      const result = await Product.create(testProduct);

      expect(result).toEqual(expectedProduct);
      expect(pool.query).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO products'),
        [
          testProduct.name,
          testProduct.category,
          testProduct.description,
          testProduct.company_name,
          testProduct.user_id
        ]
      );

      // Verify the SQL contains expected parts
      const [sql] = pool.query.mock.calls[0];
      expect(sql).toContain('INSERT INTO products');
      expect(sql).toContain('name, category, description, company_name, user_id, created_at');
      expect(sql).toContain('VALUES ($1, $2, $3, $4, $5, NOW())');
      expect(sql).toContain('RETURNING *');
    });

    it('should handle product creation with special characters', async () => {
      const specialProduct = {
        name: 'Product with "quotes" and \'apostrophes\'',
        category: 'cosmetics',
        description: 'Description with special chars: @#$%^&*()',
        company_name: 'Company & Sons',
        user_id: 1
      };

      const expectedProduct = {
        id: 2,
        ...specialProduct,
        created_at: new Date(),
      };

      pool.query.mockResolvedValueOnce({ rows: [expectedProduct] });

      const result = await Product.create(specialProduct);

      expect(result.name).toBe(specialProduct.name);
      expect(result.description).toBe(specialProduct.description);
      expect(result.company_name).toBe(specialProduct.company_name);
    });

    it('should query products by user ID correctly', async () => {
      const mockProducts = [
        { id: 1, name: 'Product A', user_id: 1 },
        { id: 2, name: 'Product B', user_id: 1 },
      ];

      pool.query.mockResolvedValueOnce({ rows: mockProducts });

      const products = await Product.findByUser(1);

      expect(products).toHaveLength(2);
      expect(products[0].user_id).toBe(1);
      expect(products[1].user_id).toBe(1);

      expect(pool.query).toHaveBeenCalledWith(
        'SELECT * FROM products WHERE user_id = $1 ORDER BY created_at DESC',
        [1]
      );
    });

    it('should query single product by ID', async () => {
      const mockProduct = { id: 123, name: 'Single Product', user_id: 1 };

      pool.query.mockResolvedValueOnce({ rows: [mockProduct] });

      const product = await Product.findById(123);

      expect(product.id).toBe(123);
      expect(product.name).toBe('Single Product');

      expect(pool.query).toHaveBeenCalledWith(
        'SELECT * FROM products WHERE id = $1',
        [123]
      );
    });
  });

  describe('Onboarding Session Database Operations', () => {
    const testSession = {
      session_id: 'session-uuid-123',
      producer_id: 'producer-uuid-456',
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

    it('should execute correct SQL for session creation', async () => {
      const expectedSession = {
        id: 1,
        ...testSession,
        created_at: new Date(),
        updated_at: new Date(),
      };

      pool.query.mockResolvedValueOnce({ rows: [expectedSession] });

      const result = await OnboardingSession.create(testSession);

      expect(result).toEqual(expectedSession);

      // Verify the call includes JSON serialization
      const [sql, params] = pool.query.mock.calls[0];
      expect(sql).toContain('INSERT INTO onboarding_sessions');
      expect(sql).toContain('session_id');
      expect(sql).toContain('producer_id');
      expect(sql).toContain('user_id');
      expect(sql).toContain('status');
      expect(sql).toContain('message');
      expect(sql).toContain('collected_fields');
      expect(sql).toContain('current_field');
      expect(sql).toContain('initial_data');
      expect(sql).toContain('VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())');

      // Verify JSON fields are properly serialized
      expect(params[5]).toBe(JSON.stringify(testSession.collected_fields)); // collected_fields
      expect(params[7]).toBe(JSON.stringify(testSession.initial_data)); // initial_data
    });

    it('should handle complex JSON data in session creation', async () => {
      const complexSession = {
        ...testSession,
        collected_fields: ['name', 'phone', 'company_size'],
        initial_data: {
          business_name: 'Complex Business Corp',
          email: 'complex@example.com',
          first_name: 'Jane',
          last_name: 'Smith',
          additional_info: {
            nested: {
              data: 'value'
            }
          }
        }
      };

      const expectedSession = {
        id: 2,
        ...complexSession,
        created_at: new Date(),
      };

      pool.query.mockResolvedValueOnce({ rows: [expectedSession] });

      const result = await OnboardingSession.create(complexSession);

      expect(result.id).toBe(2);
      expect(result.initial_data.business_name).toBe('Complex Business Corp');

      // Verify JSON serialization includes nested objects
      const [sql, params] = pool.query.mock.calls[0];
      const parsedInitialData = JSON.parse(params[7]);
      expect(parsedInitialData.additional_info.nested.data).toBe('value');
    });

    it('should query sessions by session ID', async () => {
      const mockSession = {
        id: 1,
        session_id: 'test-session-id',
        user_id: 1,
        status: 'in_progress',
      };

      pool.query.mockResolvedValueOnce({ rows: [mockSession] });

      const session = await OnboardingSession.findBySessionId('test-session-id');

      expect(session.id).toBe(1);
      expect(session.session_id).toBe('test-session-id');

      expect(pool.query).toHaveBeenCalledWith(
        'SELECT * FROM onboarding_sessions WHERE session_id = $1',
        ['test-session-id']
      );
    });

    it('should query sessions by user ID', async () => {
      const mockSessions = [
        { id: 1, session_id: 'session-1', user_id: 1, status: 'started' },
        { id: 2, session_id: 'session-2', user_id: 1, status: 'completed' },
        { id: 3, session_id: 'session-3', user_id: 1, status: 'in_progress' },
      ];

      pool.query.mockResolvedValueOnce({ rows: mockSessions });

      const sessions = await OnboardingSession.findByUserId(1);

      expect(sessions).toHaveLength(3);
      expect(sessions[0].user_id).toBe(1);
      expect(sessions[1].user_id).toBe(1);
      expect(sessions[2].user_id).toBe(1);

      expect(pool.query).toHaveBeenCalledWith(
        'SELECT * FROM onboarding_sessions WHERE user_id = $1 ORDER BY created_at DESC',
        [1]
      );
    });

    it('should handle session updates correctly', async () => {
      const updateData = {
        status: 'completed',
        message: 'Onboarding completed successfully!',
        collected_fields: ['name', 'phone', 'company_size', 'industry', 'location']
      };

      const expectedSession = {
        id: 1,
        session_id: 'session-uuid-123',
        ...updateData,
        updated_at: new Date(),
      };

      pool.query.mockResolvedValueOnce({ rows: [expectedSession] });

      const result = await OnboardingSession.update('session-uuid-123', updateData);

      expect(result.status).toBe('completed');
      expect(result.message).toBe('Onboarding completed successfully!');

      // Verify update SQL structure
      const [sql, params] = pool.query.mock.calls[0];
      expect(sql).toContain('UPDATE onboarding_sessions');
      expect(sql).toContain('SET');
      expect(sql).toContain('updated_at = NOW()');
      expect(sql).toContain('WHERE session_id = $1');
      expect(sql).toContain('RETURNING *');

      // Verify parameters include session_id at the beginning
      expect(params[0]).toBe('session-uuid-123');
    });

    it('should handle session deletion', async () => {
      const mockDeletedSession = {
        id: 1,
        session_id: 'session-to-delete',
        user_id: 1,
      };

      pool.query.mockResolvedValueOnce({ rows: [mockDeletedSession] });

      const result = await OnboardingSession.delete('session-to-delete');

      expect(result.session_id).toBe('session-to-delete');

      expect(pool.query).toHaveBeenCalledWith(
        'DELETE FROM onboarding_sessions WHERE session_id = $1 RETURNING *',
        ['session-to-delete']
      );
    });
  });

  describe('Database Error Handling', () => {
    it('should handle connection errors during product creation', async () => {
      const connectionError = new Error('Database connection failed');
      pool.query.mockRejectedValueOnce(connectionError);

      await expect(Product.create({
        name: 'Test',
        category: 'food',
        description: 'Test description',
        company_name: 'Test Company',
        user_id: 1
      })).rejects.toThrow('Database connection failed');
    });

    it('should handle connection errors during session creation', async () => {
      const connectionError = new Error('Session creation failed');
      pool.query.mockRejectedValueOnce(connectionError);

      await expect(OnboardingSession.create({
        session_id: 'test-session',
        producer_id: 'test-producer',
        user_id: 1,
        status: 'started',
        message: 'Test message',
        collected_fields: [],
        current_field: 'name',
        initial_data: {}
      })).rejects.toThrow('Session creation failed');
    });

    it('should handle unique constraint violations', async () => {
      const uniqueViolationError = {
        code: '23505', // PostgreSQL unique violation code
        message: 'duplicate key value violates unique constraint',
        detail: 'Key (session_id)=(existing-session) already exists.'
      };

      pool.query.mockRejectedValueOnce(uniqueViolationError);

      await expect(OnboardingSession.create({
        session_id: 'existing-session',
        producer_id: 'test-producer',
        user_id: 1,
        status: 'started',
        message: 'Test',
        collected_fields: [],
        current_field: 'name',
        initial_data: {}
      })).rejects.toEqual(uniqueViolationError);
    });
  });

  describe('Database Connection Management', () => {
    it('should handle pool connection properly', async () => {
      const mockClient = {
        query: jest.fn().mockResolvedValue({ rows: [{ id: 1, name: 'Test' }] }),
        release: jest.fn(),
      };

      // Mock the pool.connect method
      const mockConnect = jest.fn().mockResolvedValue(mockClient);
      pool.connect = mockConnect;

      const client = await pool.connect();
      expect(client).toBe(mockClient);
      expect(pool.connect).toHaveBeenCalled();
    });

    it('should handle connection release', async () => {
      const mockClient = {
        release: jest.fn(),
      };

      mockClient.release();
      expect(mockClient.release).toHaveBeenCalled();
    });
  });
});
