/**
 * FraudGuard Node.js SDK
 * Easy integration for fraud detection in Node.js applications
 */

const axios = require('axios');

class FraudGuardError extends Error {
  constructor(message) {
    super(message);
    this.name = 'FraudGuardError';
  }
}

class RateLimitError extends FraudGuardError {
  constructor(message, retryAfter) {
    super(message);
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
  }
}

class ValidationError extends FraudGuardError {
  constructor(message) {
    super(message);
    this.name = 'ValidationError';
  }
}

class FraudGuardClient {
  /**
   * Initialize FraudGuard client
   * @param {string} apiKey - Your FraudGuard API key
   * @param {string} baseUrl - API base URL (default: http://localhost:8000)
   */
  constructor(apiKey, baseUrl = 'http://localhost:8000') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json'
      },
      timeout: 10000
    });
  }

  /**
   * Analyze a transaction for fraud risk
   * @param {Object} transaction - Transaction data
   * @returns {Promise<Object>} Fraud prediction result
   */
  async analyzeTransaction(transaction) {
    try {
      const response = await this.client.post('/v1/ml/predict', transaction);
      return response.data;
    } catch (error) {
      if (error.response) {
        if (error.response.status === 429) {
          throw new RateLimitError('Rate limit exceeded', error.response.data.retry_after);
        } else if (error.response.status === 422) {
          throw new ValidationError(`Invalid transaction data: ${error.response.data.detail}`);
        } else {
          throw new FraudGuardError(`API error: ${error.response.data.detail || error.message}`);
        }
      } else {
        throw new FraudGuardError(`Network error: ${error.message}`);
      }
    }
  }

  /**
   * Ingest a transaction for real-time monitoring
   * @param {Object} transaction - Transaction data
   * @returns {Promise<Object>} Ingestion result
   */
  async ingestTransaction(transaction) {
    try {
      const response = await this.client.post('/api/v1/ingestion/transactions', transaction);
      return response.data;
    } catch (error) {
      if (error.response) {
        if (error.response.status === 429) {
          const retryAfter = error.response.data.retry_after || 60;
          throw new RateLimitError(`Rate limit exceeded. Retry after ${retryAfter} seconds`, retryAfter);
        } else if (error.response.status === 400) {
          throw new ValidationError(`Invalid transaction: ${error.response.data.detail}`);
        } else {
          throw new FraudGuardError(`Ingestion failed: ${error.response.data.detail || error.message}`);
        }
      } else {
        throw new FraudGuardError(`Network error: ${error.message}`);
      }
    }
  }

  /**
   * Ingest multiple transactions at once
   * @param {Array<Object>} transactions - Array of transaction objects (max 100)
   * @returns {Promise<Object>} Batch results
   */
  async batchIngest(transactions) {
    if (transactions.length > 100) {
      throw new ValidationError('Batch size cannot exceed 100 transactions');
    }

    try {
      const response = await this.client.post('/api/v1/ingestion/transactions/batch', transactions);
      return response.data;
    } catch (error) {
      if (error.response) {
        if (error.response.status === 429) {
          throw new RateLimitError('Rate limit exceeded', error.response.data.retry_after);
        } else {
          throw new FraudGuardError(`Batch ingestion failed: ${error.response.data.detail || error.message}`);
        }
      } else {
        throw new FraudGuardError(`Network error: ${error.message}`);
      }
    }
  }

  /**
   * Get fraud alerts
   * @param {string} accountId - Filter by account ID (optional)
   * @param {number} limit - Maximum number of alerts
   * @returns {Promise<Array>} List of alerts
   */
  async getAlerts(accountId = null, limit = 100) {
    const params = { limit };
    if (accountId) {
      params.account_id = accountId;
    }

    try {
      const response = await this.client.get('/v1/alerts', { params });
      return response.data;
    } catch (error) {
      if (error.response) {
        throw new FraudGuardError(`Failed to get alerts: ${error.response.data.detail || error.message}`);
      } else {
        throw new FraudGuardError(`Network error: ${error.message}`);
      }
    }
  }

  /**
   * Check API health
   * @returns {Promise<Object>} Health status
   */
  async healthCheck() {
    try {
      const response = await this.client.get('/');
      return response.data;
    } catch (error) {
      throw new FraudGuardError(`Health check failed: ${error.message}`);
    }
  }
}

module.exports = {
  FraudGuardClient,
  FraudGuardError,
  RateLimitError,
  ValidationError
};

