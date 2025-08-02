// src/middleware/security.js
const crypto = require('crypto');

const securityMiddleware = (req, res, next) => {
  // Remove server signature
  res.removeHeader('X-Powered-By');
  
  // Add security headers
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
  
  // Content type validation for JSON requests
  if (req.method === 'POST' || req.method === 'PUT') {
    const contentType = req.get('Content-Type');
    if (contentType && !contentType.includes('application/json')) {
      if (!contentType.includes('multipart/form-data')) {
        return res.status(400).json({ error: 'Invalid content type' });
      }
    }
  }
  
  // Request size validation
  const contentLength = parseInt(req.get('Content-Length') || '0');
  if (contentLength > 2 * 1024 * 1024) { // 2MB limit
    return res.status(413).json({ error: 'Request too large' });
  }
  
  // Sanitize common injection patterns
  const suspiciousPatterns = [
    /(<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>)/gi,
    /(javascript:|data:text\/html|vbscript:|onload=|onerror=)/gi,
    /(union\s+select|drop\s+table|truncate\s+table|delete\s+from)/gi,
    /(\$\{|\#\{|<%=|<%|%>)/gi
  ];
  
  const checkForInjection = (obj) => {
    if (typeof obj === 'string') {
      return suspiciousPatterns.some(pattern => pattern.test(obj));
    }
    if (typeof obj === 'object' && obj !== null) {
      return Object.values(obj).some(checkForInjection);
    }
    return false;
  };
  
  if (req.body && checkForInjection(req.body)) {
    return res.status(400).json({ error: 'Invalid input detected' });
  }
  
  next();
};

// Input sanitization
const sanitizeInput = (input) => {
  if (typeof input === 'string') {
    return input
      .trim()
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/[<>]/g, '')
      .substring(0, 10000); // Max length
  }
  return input;
};

const sanitizeObject = (obj) => {
  if (typeof obj !== 'object' || obj === null) return obj;
  
  const sanitized = {};
  for (const [key, value] of Object.entries(obj)) {
    if (typeof value === 'string') {
      sanitized[key] = sanitizeInput(value);
    } else if (typeof value === 'object') {
      sanitized[key] = sanitizeObject(value);
    } else {
      sanitized[key] = value;
    }
  }
  return sanitized;
};

module.exports = { securityMiddleware, sanitizeInput, sanitizeObject };