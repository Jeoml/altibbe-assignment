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
const onboardingRoutes = require('./routes/onboarding');
const { errorHandler } = require('./middleware/errorHandler');
const { securityMiddleware } = require('./middleware/security');

const swaggerUi = require('swagger-ui-express');
const swaggerJsdoc = require('swagger-jsdoc');

const app = express();
const PORT = process.env.PORT || 5002;

// Dynamic server URL based on environment
const getServerUrl = () => {
  // Force Railway URL if we're clearly on Railway (check for Railway-specific indicators)
  const host = process.env.RAILWAY_PROJECT_ID || process.env.RAILWAY_STATIC_URL ||
               (process.env.HOSTNAME && process.env.HOSTNAME.includes('railway'));

  if (host || process.env.NODE_ENV === 'production') {
    const railwayUrl = process.env.RAILWAY_STATIC_URL ||
                      `https://altibbe-assignment-production-07f7.up.railway.app`;
    console.log('✅ Using Railway URL:', railwayUrl);
    return railwayUrl;
  }

  // Local development
  const localUrl = `http://localhost:${PORT}`;
  console.log('✅ Using local URL:', localUrl);
  return localUrl;
};

// Force Railway URL for now (temporary fix)
const FORCE_RAILWAY_URL = 'https://altibbe-assignment-production-07f7.up.railway.app';

// Manual override - uncomment this line if Railway detection fails
const FORCE_RAILWAY_MODE = true;

// Check if we're on Railway and force the correct server
const isOnRailway = process.env.RAILWAY_PROJECT_ID || process.env.RAILWAY_STATIC_URL ||
                   (process.env.HOSTNAME && process.env.HOSTNAME.includes('railway')) ||
                   process.env.NODE_ENV === 'production' ||
                   (typeof FORCE_RAILWAY_MODE !== 'undefined' && FORCE_RAILWAY_MODE);

const swaggerOptions = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Product Transparency API',
      version: '1.0.0',
      description: 'API for generating product transparency reports'
    },
    servers: isOnRailway ? [
      { url: FORCE_RAILWAY_URL, description: 'Railway Production' }
    ] : [
      { url: `http://localhost:${PORT}`, description: 'Local Development' },
      { url: FORCE_RAILWAY_URL, description: 'Railway Production' }
    ],
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
      'https://frontend-altibbe.vercel.app',
      'http://localhost:5002',     // Alternative port
      'https://altibbe-assignment-production-07f7.up.railway.app', // Railway frontend URL
      // Add Railway backend domain dynamically
      process.env.RAILWAY_STATIC_URL,
      // Allow Railway subdomain pattern
      ...(process.env.RAILWAY_PROJECT_ID ? [`https://${process.env.RAILWAY_PROJECT_ID}.up.railway.app`] : [])
    ].filter(Boolean);

    // Allow requests with no origin (mobile apps, Postman, etc.)
    if (!origin) {
      return callback(null, true);
    }

    // Check if origin is allowed
    const isAllowed = allowedOrigins.some(allowedOrigin => {
      if (allowedOrigin === origin) return true;

      // Handle Railway subdomain pattern matching
      if (allowedOrigin.includes('railway.app') && origin.includes('railway.app')) {
        return origin.endsWith('.railway.app') || origin.endsWith('.up.railway.app');
      }

      return false;
    });

    if (isAllowed) {
      callback(null, true);
    } else {
      console.log(`❌ CORS blocked origin: ${origin}`);
      console.log(`Allowed origins:`, allowedOrigins);
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'x-session-id']
}));

// Security middleware
const isProduction = process.env.NODE_ENV === 'production';
const isRailway = process.env.RAILWAY_STATIC_URL || process.env.RAILWAY_PROJECT_ID;

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
      // Allow connections to Railway domains
      connectSrc: ["'self'", ...(isRailway ? ["https://*.railway.app"] : [])],
    },
  },
  hsts: isProduction || isRailway ? {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  } : false, // Disable HSTS in development
  // Allow cross-origin requests from Railway
  crossOriginResourcePolicy: { policy: "cross-origin" }
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

// Database keep-alive ping removed to prevent connection limit issues

// Routes
app.use('/api/products', productRoutes);
app.use('/api/questions', questionRoutes);
app.use('/api/reports', reportRoutes);
app.use('/api/auth', authRoutes);
app.use('/api/onboarding', onboardingRoutes);

// Health check with security headers
app.get('/health', (req, res) => {
  res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
  res.json({
    status: 'OK',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    env: process.env.NODE_ENV || 'development',
    railway: {
      project_id: process.env.RAILWAY_PROJECT_ID,
      static_url: process.env.RAILWAY_STATIC_URL,
      hostname: process.env.HOSTNAME
    },
    detection: {
      isOnRailway: isOnRailway,
      server_url: getServerUrl()
    }
  });
});

// Quick test endpoint
app.get('/test', (req, res) => {
  res.json({
    message: 'API is working!',
    server_url: getServerUrl(),
    timestamp: new Date().toISOString()
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
  console.log(`📚 API Documentation: http://localhost:${PORT}/docs`);
});

module.exports = app;