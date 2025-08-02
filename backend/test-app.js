// Minimal test app to isolate the issue
require('dotenv').config();
const express = require('express');

const app = express();
const PORT = process.env.PORT || 5000;

// Basic middleware
app.use(express.json());

// Test route
app.get('/test', (req, res) => {
  res.json({ message: 'Test successful' });
});

app.listen(PORT, () => {
  console.log(`Test server running on port ${PORT}`);
});
