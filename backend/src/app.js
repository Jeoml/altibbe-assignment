require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const hpp = require('hpp');
const compression = require('compression');

const productRoutes = require('./routes/products');
const questionRoutes = require('./routes/questions');
const reportRoutes = require('./routes/reports');
const authRoutes = require('./routes/auth');
const { errorHandler } = require('./middleware/errorHandler');
const { securityMiddleware } = require('./middleware/security');

const swaggerUi = require('swagger-ui-express');
const swaggerJsdoc = require('swagger-jsdoc');

const app = express();
const PORT = process.env.PORT || 5002;

const swaggerOptions = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Product Transparency API',
      version: '1.0.0',
      description: 'API for generating product transparency reports'
    },
    servers: [{ url: `http://localhost:${PORT}` }],
    components: {
      securitySchemes: {
        bearerAuth: { type: 'http', scheme: 'bearer', bearerFormat: 'JWT' }
      }
    }
  },
  apis: ['./src/routes/*.js']
};

const swaggerSpec = swaggerJsdoc(swaggerOptions);

// Trust proxy (for rate limiting behind reverse proxy)
app.set('trust proxy', 1);

// CORS with strict settings - Apply early
app.use(cors({
  origin: function (origin, callback) {
    const allowedOrigins = [
      process.env.FRONTEND_URL,
      'http://localhost:3001',
      'https://localhost:3001',
      `http://localhost:${PORT}`, // Allow Swagger UI origin
      'http://localhost:5000',     // Explicit port 5000 for Swagger
      'http://localhost:5002'      // Alternative port
    ].filter(Boolean);
    
    // Allow requests with no origin (mobile apps, Postman, etc.)
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      console.log(`❌ CORS blocked origin: ${origin}`);
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'x-session-id']
}));

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: {
    error: 'Too many requests from this IP, please try again later.'
  },
  standardHeaders: true,
  legacyHeaders: false,
});

const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5, // limit each IP to 5 auth requests per windowMs
  message: {
    error: 'Too many authentication attempts, please try again later.'
  }
});

app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));
app.get('/api-docs.json', (req, res) => res.json(swaggerSpec));

// Apply rate limiting after Swagger setup
app.use(limiter);
app.use('/api/auth', authLimiter);

// Security middleware - XSS protection now handled by helmet
// app.use(xss()); // Removed deprecated xss-clean package
app.use(hpp()); // Prevent HTTP Parameter Pollution
app.use(compression()); // Compress responses

// Request logging (exclude sensitive data)
app.use(morgan('combined', {
  skip: (req) => req.path.includes('/auth'),
  stream: {
    write: (message) => {
      // Remove sensitive data from logs
      const sanitized = message.replace(/password[^&\s]*/gi, 'password=***');
      console.log(sanitized.trim());
    }
  }
}));

// Body parsing with strict limits
app.use(express.json({ 
  limit: '2mb',
  verify: (req, res, buf) => {
    try {
      JSON.parse(buf);
    } catch (e) {
      throw new Error('Invalid JSON');
    }
  }
}));
app.use(express.urlencoded({ extended: true, limit: '2mb' }));

// Additional security middleware
app.use(securityMiddleware);

// Keep-alive ping mechanism
const keepAlive = () => {
  setInterval(() => {
    // Ping database to keep connection alive (only if connected)
    require('./config/database').query('SELECT 1')
      .then(() => console.log('🏓 Database keepalive ping successful'))
      .catch(err => {
        // Don't log detailed errors for expected disconnections
        if (err.code === 'ECONNREFUSED' || err.message.includes('timeout')) {
          console.log('⏳ Database not available for keepalive ping');
        } else {
          console.error('❌ Database keepalive failed:', err.message);
        }
      });
  }, 3 * 60 * 1000); // Every 3 minutes
};

// Start keepalive
keepAlive();

// Routes
app.use('/api/products', productRoutes);
app.use('/api/questions', questionRoutes);
app.use('/api/reports', reportRoutes);
app.use('/api/auth', authRoutes);

// Health check with security headers
app.get('/health', (req, res) => {
  res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
  res.json({ 
    status: 'OK', 
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    env: process.env.NODE_ENV || 'development'
  });
});

// Error handling
app.use(errorHandler);

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ 
    error: 'Route not found',
    path: req.originalUrl,
    method: req.method
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully');
  process.exit(0);
});

app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`🔒 Security: Rate limiting, CORS, XSS protection enabled`);
  console.log(`🏓 Keep-alive: Database ping every 3 minutes`);
  console.log(`📚 API Documentation: http://localhost:${PORT}/docs`);
});

module.exports = app;