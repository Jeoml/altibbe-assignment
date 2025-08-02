// src/middleware/auth.js
const jwt = require('jsonwebtoken');
const crypto = require('crypto');

const JWT_SECRET = process.env.JWT_SECRET || crypto.randomBytes(64).toString('hex');
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '24h';
const JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET || crypto.randomBytes(64).toString('hex');

// Token blacklist (in production, use Redis)
const tokenBlacklist = new Set();

const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  // Check if token is blacklisted
  if (tokenBlacklist.has(token)) {
    return res.status(401).json({ error: 'Token has been revoked' });
  }

  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) {
      if (err.name === 'TokenExpiredError') {
        return res.status(401).json({ error: 'Token expired' });
      }
      return res.status(403).json({ error: 'Invalid token' });
    }
    
    // Check token age for additional security
    const tokenAge = Date.now() - (user.iat * 1000);
    const maxAge = 24 * 60 * 60 * 1000; // 24 hours
    
    if (tokenAge > maxAge) {
      return res.status(401).json({ error: 'Token too old, please refresh' });
    }
    
    req.user = user;
    next();
  });
};

const generateTokens = (userId, email) => {
  const payload = { 
    id: userId, 
    email,
    iat: Math.floor(Date.now() / 1000)
  };
  
  const accessToken = jwt.sign(payload, JWT_SECRET, { expiresIn: JWT_EXPIRES_IN });
  const refreshToken = jwt.sign(payload, JWT_REFRESH_SECRET, { expiresIn: '7d' });
  
  return { accessToken, refreshToken };
};

const revokeToken = (token) => {
  tokenBlacklist.add(token);
  
  // Clean old tokens every hour
  if (tokenBlacklist.size % 100 === 0) {
    setTimeout(() => {
      const oneHourAgo = Date.now() - (60 * 60 * 1000);
      for (const oldToken of tokenBlacklist) {
        try {
          const decoded = jwt.decode(oldToken);
          if (decoded && decoded.iat * 1000 < oneHourAgo) {
            tokenBlacklist.delete(oldToken);
          }
        } catch (e) {
          tokenBlacklist.delete(oldToken);
        }
      }
    }, 0);
  }
};

module.exports = { 
  authenticateToken, 
  generateTokens, 
  revokeToken,
  JWT_SECRET,
  JWT_REFRESH_SECRET 
};