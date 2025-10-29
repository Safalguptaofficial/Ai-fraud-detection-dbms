// Seed data for MongoDB

db = db.getSiblingDB('frauddb');

// Insert fraud cases
db.fraud_cases.insertMany([
    {
        caseId: 'CASE-001',
        accountId: 1,
        txnIds: [1001, 1002],
        investigator: 'alice@bank.com',
        notes: [
            {
                author: 'alice@bank.com',
                content: 'Suspicious CNP transaction pattern. Midnight withdrawal >$5K.',
                createdAt: new Date()
            },
            {
                author: 'alice@bank.com',
                content: 'Customer claims card was lost. Investigating ATM location.',
                createdAt: new Date(Date.now() - 3600000)
            }
        ],
        attachments: [
            {
                gridFsId: 'att001',
                filename: 'atm_camera_footage.mp4',
                contentType: 'video/mp4'
            }
        ],
        status: 'OPEN',
        tags: ['CNP', 'MIDNIGHT_5K', 'ATM'],
        createdAt: new Date(Date.now() - 86400000),
        updatedAt: new Date()
    },
    {
        caseId: 'CASE-002',
        accountId: 2,
        txnIds: [2001, 2002],
        investigator: 'bob@bank.com',
        notes: [
            {
                author: 'bob@bank.com',
                content: 'Geographical jump detected: NYC to LA in 3 hours. Impossible travel?',
                createdAt: new Date()
            }
        ],
        attachments: [],
        status: 'INVESTIGATING',
        tags: ['GEO_JUMP', 'TRAVEL'],
        createdAt: new Date(Date.now() - 7200000),
        updatedAt: new Date()
    }
]);

// Insert SAR reports
db.sar_reports.insertMany([
    {
        reportId: 'SAR-2025-001',
        accountId: 1,
        suspiciousActivity: 'Multiple high-value cash withdrawals at unusual hours',
        amount: 15000.00,
        reportDate: new Date(),
        filedBy: 'alice@bank.com',
        status: 'SUBMITTED'
    }
]);

// Insert customer complaints
db.customer_complaints.insertMany([
    {
        complaintId: 'COMP-2025-001',
        customerId: 'C001',
        accountId: 1,
        subject: 'Unauthorized ATM withdrawal',
        description: 'I received an alert about a $7,500 withdrawal I did not make. Please freeze my account.',
        status: 'OPEN',
        priority: 'HIGH',
        createdAt: new Date()
    }
]);

print('MongoDB seed data inserted successfully.');
print(`Inserted ${db.fraud_cases.countDocuments()} fraud cases`);
print(`Inserted ${db.sar_reports.countDocuments()} SAR reports`);
print(`Inserted ${db.customer_complaints.countDocuments()} customer complaints`);

