// MongoDB Collections for Fraud Detection

// Use frauddb database
db = db.getSiblingDB('frauddb');

// Drop existing collections
db.fraud_cases.drop();
db.sar_reports.drop();
db.customer_complaints.drop();
db.system_logs.drop();

// Create collections with validation
db.createCollection('fraud_cases', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['caseId', 'accountId', 'status', 'createdAt'],
            properties: {
                caseId: { bsonType: 'string' },
                accountId: { bsonType: 'int' },
                txnIds: { bsonType: 'array' },
                investigator: { bsonType: 'string' },
                notes: { bsonType: 'array' },
                attachments: { bsonType: 'array' },
                status: { 
                    enum: ['OPEN', 'INVESTIGATING', 'RESOLVED', 'ESCALATED'] 
                },
                tags: { bsonType: 'array' },
                createdAt: { bsonType: 'date' },
                updatedAt: { bsonType: 'date' }
            }
        }
    }
});

db.createCollection('sar_reports', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['reportId', 'reportDate'],
            properties: {
                reportId: { bsonType: 'string' },
                accountId: { bsonType: 'int' },
                suspiciousActivity: { bsonType: 'string' },
                amount: { bsonType: 'double' },
                reportDate: { bsonType: 'date' },
                filedBy: { bsonType: 'string' },
                status: { 
                    enum: ['DRAFT', 'SUBMITTED', 'ACCEPTED'] 
                }
            }
        }
    }
});

db.createCollection('customer_complaints', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['complaintId', 'customerId', 'createdAt'],
            properties: {
                complaintId: { bsonType: 'string' },
                customerId: { bsonType: 'string' },
                accountId: { bsonType: 'int' },
                subject: { bsonType: 'string' },
                description: { bsonType: 'string' },
                status: { 
                    enum: ['OPEN', 'IN_PROGRESS', 'RESOLVED'] 
                },
                priority: { 
                    enum: ['LOW', 'MEDIUM', 'HIGH'] 
                },
                createdAt: { bsonType: 'date' }
            }
        }
    }
});

db.createCollection('system_logs');

// Create indexes
// Text index for searching case notes
db.fraud_cases.createIndex({ 
    'notes.content': 'text',
    'tags': 1,
    'createdAt': -1 
});

// Compound indexes for querying
db.fraud_cases.createIndex({ accountId: 1, createdAt: -1 });
db.fraud_cases.createIndex({ status: 1, createdAt: -1 });
db.fraud_cases.createIndex({ investigator: 1 });

db.sar_reports.createIndex({ reportId: 1 });
db.sar_reports.createIndex({ accountId: 1, reportDate: -1 });

db.customer_complaints.createIndex({ complaintId: 1 });
db.customer_complaints.createIndex({ customerId: 1, createdAt: -1 });

// TTL index for system logs (30 days retention)
db.system_logs.createIndex({ createdAt: 1 }, { expireAfterSeconds: 2592000 });

print('MongoDB collections and indexes created successfully.');

