# API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication

### JWT (Web Portal)
```bash
# Login endpoint would return JWT
# Use in Authorization header:
Authorization: Bearer <token>
```

### API Key (Service-to-Service)
```bash
x-api-key: dev-key
```

## Endpoints

### POST /v1/accounts

Create a new account.

**Request:**
```json
{
  "customer_id": "C12345"
}
```

**Response:** 201
```json
{
  "id": 1,
  "customer_id": "C12345",
  "status": "ACTIVE",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": null
}
```

### POST /v1/transactions

Create a transaction. Triggers fraud detection rules automatically.

**Request:**
```json
{
  "account_id": 1,
  "amount": 7000,
  "currency": "USD",
  "merchant": "ATM-CORP",
  "mcc": "6011",
  "channel": "ATM",
  "lat": 40.7128,
  "lon": -74.0060,
  "city": "NYC",
  "country": "US",
  "txn_time": "2025-01-15T00:15:00Z"
}
```

**Response:** 201
```json
{
  "id": 42,
  "account_id": 1,
  "amount": 7000,
  "status": "REVIEW",
  ...
}
```

**Note:** If a fraud rule triggers, the status will be set to "REVIEW" and an alert will be created.

### GET /v1/alerts

Get fraud alerts.

**Query Parameters:**
- `status`: "open" or "all" (default: all)

**Example:**
```bash
curl http://localhost:8000/v1/alerts?status=open \
  -H "Authorization: Bearer <token>"
```

**Response:** 200
```json
[
  {
    "id": 1,
    "account_id": 1,
    "txn_id": 42,
    "rule_code": "MIDNIGHT_5K",
    "severity": "HIGH",
    "reason": "High-amount transaction between 00:00–05:00",
    "created_at": "2025-01-15T00:16:00Z",
    "handled": false
  }
]
```

### GET /v1/analytics/anomalies

Get anomaly events from OLAP database.

**Query Parameters:**
- `rule`: Filter by rule name (e.g., "GEO_JUMP")
- `date_from`: Start date (ISO format)
- `date_to`: End date (ISO format)
- `severity`: Filter by severity
- `account_id`: Filter by account

**Example:**
```bash
curl "http://localhost:8000/v1/analytics/anomalies?rule=GEO_JUMP&date_from=2025-01-01&date_to=2025-01-07" \
  -H "Authorization: Bearer <token>"
```

**Response:** 200
```json
[
  {
    "id": "uuid",
    "account_id": 2,
    "txn_id": 2003,
    "rule": "GEO_JUMP",
    "score": 0.95,
    "detected_at": "2025-01-15T12:00:00Z",
    "severity": "MEDIUM",
    "extra": {
      "distance_km": 4500,
      "time_hours": 3
    }
  }
]
```

### POST /v1/cases

Create a fraud case.

**Request:**
```json
{
  "accountId": 1,
  "txnIds": [42, 43],
  "tags": ["CNP", "ATM"],
  "notes": "Suspicious activity detected"
}
```

### GET /v1/cases/search

Full-text search cases by notes content.

**Query Parameters:**
- `q`: Search query string

**Example:**
```bash
curl "http://localhost:8000/v1/cases/search?q=ATM%20skimmer" \
  -H "Authorization: Bearer <token>"
```

### POST /v1/cases/{caseId}/notes

Add a note to a case.

**Request:**
```json
{
  "author": "alice@bank.com",
  "content": "Confirmed with customer: card was lost"
}
```

### POST /v1/cases/{caseId}/attachments

Upload a file attachment to a case.

**Request:**
```
Content-Type: multipart/form-data

file: <binary>
```

**Response:** 200
```json
{
  "message": "Attachment uploaded",
  "attachment": {
    "gridFsId": "abc123",
    "filename": "evidence.jpg",
    "contentType": "image/jpeg"
  }
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid API key"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal error"
}
```

## Rate Limiting

- 100 requests per minute per IP
- Service-to-service: 1000 requests per minute per API key

Rate limit headers:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset time (Unix timestamp)

