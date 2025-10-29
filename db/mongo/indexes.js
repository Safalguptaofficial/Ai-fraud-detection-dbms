// Additional MongoDB Indexes

db = db.getSiblingDB('frauddb');

// Ensure all important indexes exist
db.fraud_cases.createIndex({ caseId: 1 }, { unique: true });
db.fraud_cases.createIndex({ tags: 1 });

print('Additional indexes created.');

