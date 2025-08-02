const monitoringService = {
  // Database connection monitoring
  startDatabaseMonitoring() {
    const db = require('../config/database');
    
    setInterval(async () => {
      try {
        const health = await db.checkHealth();
        if (!health.healthy) {
          console.error('🚨 Database health check failed:', health.error);
          // In production: send alert to monitoring service
        }
      } catch (error) {
        console.error('🚨 Health check error:', error);
      }
    }, 3 * 60 * 1000); // Every 3 minutes
  },

  // Memory usage monitoring
  startMemoryMonitoring() {
    setInterval(() => {
      const memUsage = process.memoryUsage();
      const memUsageMB = {
        rss: Math.round(memUsage.rss / 1024 / 1024),
        heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024),
        heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024),
        external: Math.round(memUsage.external / 1024 / 1024)
      };
      
      // Log if memory usage is high
      if (memUsageMB.heapUsed > 200) { // 200MB threshold
        console.warn('⚠️ High memory usage:', memUsageMB);
      }
    }, 5 * 60 * 1000); // Every 5 minutes
  },

  // Error rate monitoring
  errorCount: 0,
  successCount: 0,
  
  logRequest(success = true) {
    if (success) {
      this.successCount++;
    } else {
      this.errorCount++;
    }
    
    // Reset counters every hour and log stats
    if ((this.errorCount + this.successCount) % 1000 === 0) {
      const errorRate = (this.errorCount / (this.errorCount + this.successCount)) * 100;
      console.log(`📊 Error rate: ${errorRate.toFixed(2)}% (${this.errorCount}/${this.errorCount + this.successCount})`);
      
      if (errorRate > 10) { // Alert if error rate > 10%
        console.error('🚨 High error rate detected!');
      }
    }
  }
};

module.exports = monitoringService;// package.json
