/**
 * Express.js Integration Example
 * Process payments with fraud detection
 */
const express = require('express');
const { FraudGuardClient } = require('@fraudguard/sdk');

const app = express();
app.use(express.json());

// Initialize FraudGuard client
const client = new FraudGuardClient(
  'fgk_live_your_api_key_here',
  'https://api.fraudguard.com'
);

app.post('/process_payment', async (req, res) => {
  try {
    const { customer_id, amount, currency = 'USD' } = req.body;
    
    // Analyze fraud risk
    const fraudResult = await client.analyzeTransaction({
      amount: amount,
      account_id: customer_id,
      merchant: 'My Store',
      currency: currency
    });
    
    // Decision logic
    if (fraudResult.risk_score >= 70) {
      return res.status(400).json({
        status: 'declined',
        reason: 'High fraud risk detected',
        fraud_score: fraudResult.risk_score
      });
    }
    
    if (fraudResult.risk_score >= 40) {
      return res.status(202).json({
        status: 'requires_verification',
        fraud_score: fraudResult.risk_score,
        message: 'Additional verification required'
      });
    }
    
    // Low risk - process payment
    // ... your payment processing code ...
    
    // Ingest for monitoring
    const ingestResult = await client.ingestTransaction({
      account_id: customer_id,
      amount: amount,
      merchant: 'My Store',
      currency: currency
    });
    
    res.json({
      status: 'approved',
      transaction_id: ingestResult.transaction_id,
      fraud_score: ingestResult.fraud_score
    });
    
  } catch (error) {
    console.error('Payment processing error:', error);
    res.status(500).json({
      status: 'error',
      message: error.message
    });
  }
});

app.listen(3000, () => {
  console.log('Payment API running on port 3000');
});

