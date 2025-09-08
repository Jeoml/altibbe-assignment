const express = require('express');
const jwt = require('jsonwebtoken');
const pool = require('../src/config/database');
const Product = require('../src/models/Product');
const OnboardingSession = require('../src/models/OnboardingSession');
const { aiService } = require('../src/services/aiService');

// Mock AI service to avoid external API calls
jest.mock('../src/services/aiService', () => ({
  aiService: {
    generateQuestions: jest.fn().mockResolvedValue([]),
  },
}));

// Mock database for isolation
jest.mock('../src/config/database', () => ({
  query: jest.fn(),
  getClient: jest.fn(),
  pool: {
    query: jest.fn(),
    connect: jest.fn(),
    end: jest.fn(),
  },
}));

const app = express();
app.use(express.json());

// Import routes after mocking
const productRoutes = require('../src/routes/products');
const authMiddleware = require('../src/middleware/auth');

app.use('/api/products', productRoutes);

// Helper to create test user and token
const createTestUser = () => {
  const user = { id: 1, email: 'test@example.com' };
  const token = jwt.sign(user, 'test-secret');
  return { user, token };
};

describe('Product Registration API', () => {
  let testUser, token;

  beforeAll(() => {
    // Create test user and token once for all tests
    const result = createTestUser();
    testUser = result.user;
    token = result.token;
  });

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();

    // Mock auth middleware
    authMiddleware.authenticateToken = jest.fn((req, res, next) => {
      req.user = testUser;
      next();
    });
  });

  afterAll(async () => {
    // Clean up database connections - skip if pool.end is not available
    if (pool.end && typeof pool.end === 'function') {
      await pool.end();
    }
  });

  describe('Product Model Tests', () => {
    const getValidProductData = () => ({
      name: 'Test Product',
      category: 'food',
      description: 'This is a test product description with more than 10 characters.',
      company_name: 'Test Company',
      user_id: testUser.id
    });

    it('should create a product successfully with valid data', async () => {
      const validProductData = getValidProductData();

      // Mock database response
      const mockProduct = {
        id: 1,
        ...validProductData,
        created_at: new Date(),
      };

      pool.query.mockResolvedValueOnce({ rows: [mockProduct] });

      const result = await Product.create(validProductData);

      expect(result).toMatchObject({
        id: 1,
        name: validProductData.name,
        category: validProductData.category,
        description: validProductData.description,
        company_name: validProductData.company_name,
        user_id: testUser.id,
      });

      // Verify database query was called correctly
      expect(pool.query).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO products'),
        [
          validProductData.name,
          validProductData.category,
          validProductData.description,
          validProductData.company_name,
          validProductData.user_id
        ]
      );
    });

    it('should handle database errors during product creation', async () => {
      const validProductData = getValidProductData();

      // Mock database error
      pool.query.mockRejectedValueOnce(new Error('Database connection failed'));

      await expect(Product.create(validProductData)).rejects.toThrow('Database connection failed');
    });

    it('should find products by user correctly', async () => {
      const mockProducts = [
        {
          id: 1,
          name: 'Product 1',
          category: 'food',
          description: 'Description 1',
          company_name: 'Company 1',
          user_id: testUser.id,
          created_at: new Date(),
        },
        {
          id: 2,
          name: 'Product 2',
          category: 'cosmetics',
          description: 'Description 2',
          company_name: 'Company 2',
          user_id: testUser.id,
          created_at: new Date(),
        },
      ];

      pool.query.mockResolvedValueOnce({ rows: mockProducts });

      const products = await Product.findByUser(testUser.id);

      expect(Array.isArray(products)).toBe(true);
      expect(products).toHaveLength(2);
      expect(products[0]).toMatchObject({
        id: 1,
        name: 'Product 1',
        category: 'food',
      });
    });

    it('should find product by ID correctly', async () => {
      const mockProduct = {
        id: 1,
        name: 'Test Product',
        category: 'food',
        description: 'Test description',
        company_name: 'Test Company',
        user_id: testUser.id,
        created_at: new Date(),
      };

      pool.query.mockResolvedValueOnce({ rows: [mockProduct] });

      const product = await Product.findById(1);

      expect(product).toMatchObject({
        id: 1,
        name: 'Test Product',
        category: 'food',
      });
    });

    it('should return null for non-existent product', async () => {
      pool.query.mockResolvedValueOnce({ rows: [] });

      const product = await Product.findById(999);

      expect(product).toBeUndefined();
    });
  });
});
