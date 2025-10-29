# 🚀 FraudGuard Installation Guide

Complete guide to install and run the AI-Powered Fraud Detection System.

---

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Software Requirements](#software-requirements)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Troubleshooting](#troubleshooting)

---

## 📦 Prerequisites

### Required Software

#### 1. **Node.js & npm**
```bash
# Check if installed
node --version  # Should be v18+ or v20+
npm --version   # Should be v9+ or v10+

# Install on macOS
brew install node

# Install on Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install on Windows
# Download from https://nodejs.org/
```

#### 2. **Python 3.11+**
```bash
# Check if installed
python3 --version  # Should be 3.11 or higher

# Install on macOS
brew install python@3.11

# Install on Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Install on Windows
# Download from https://www.python.org/downloads/
```

#### 3. **Docker & Docker Compose**
```bash
# Check if installed
docker --version
docker-compose --version

# Install on macOS
brew install --cask docker

# Install on Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose

# Install on Windows
# Download Docker Desktop from https://www.docker.com/products/docker-desktop
```

#### 4. **Git**
```bash
# Check if installed
git --version

# Install on macOS
brew install git

# Install on Ubuntu/Debian
sudo apt install git

# Install on Windows
# Download from https://git-scm.com/download/win
```

---

## 📚 Software & Library Requirements

### Backend (Python)

**Core Framework:**
- FastAPI 0.104.1
- Uvicorn 0.24.0
- Pydantic 2.5.0

**Database Drivers:**
- oracledb 1.4.2 (Oracle Instant Client)
- psycopg2-binary 2.9.9 (PostgreSQL)
- pymongo 4.6.0 (MongoDB)

**Data Processing:**
- numpy 1.26.2
- pandas 2.1.4

**API & Security:**
- python-jose 3.3.0 (JWT tokens)
- passlib 1.7.4 (Password hashing)
- python-multipart 0.0.6 (File uploads)
- python-dotenv 1.0.0 (Environment variables)

**Monitoring:**
- prometheus-client 0.19.0

**Full requirements:**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
oracledb==1.4.2
psycopg2-binary==2.9.9
pymongo==4.6.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
python-dotenv==1.0.0
prometheus-client==0.19.0
numpy==1.26.2
pandas==2.1.4
```

### Frontend (Node.js/React)

**Core Framework:**
- Next.js 14.0.4
- React 18.2.0
- TypeScript 5.3.3

**UI Libraries:**
- Tailwind CSS 3.3.6
- Lucide React 0.294.0 (Icons)
- Recharts 2.10.3 (Charts)
- React Leaflet 4.2.1 (Maps)

**State & Data:**
- @tanstack/react-query 5.13.4
- Sonner 1.2.3 (Toast notifications)

**Development:**
- ESLint 8.55.0
- PostCSS 8.4.32
- Autoprefixer 10.4.16

**Full dependencies:**
```json
{
  "dependencies": {
    "next": "14.0.4",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "lucide-react": "^0.294.0",
    "recharts": "^2.10.3",
    "leaflet": "^1.9.4",
    "react-leaflet": "^4.2.1",
    "@tanstack/react-query": "^5.13.4",
    "sonner": "^1.2.3"
  },
  "devDependencies": {
    "@types/node": "20.10.5",
    "@types/react": "18.2.45",
    "@types/react-dom": "18.2.18",
    "@types/leaflet": "^1.9.8",
    "typescript": "5.3.3",
    "tailwindcss": "3.3.6",
    "postcss": "8.4.32",
    "autoprefixer": "10.4.16",
    "eslint": "8.55.0",
    "eslint-config-next": "14.0.4"
  }
}
```

### Databases

**1. Oracle Database**
```bash
# Oracle XE (Express Edition) - Free
docker pull container-registry.oracle.com/database/express:latest

# Or Oracle 19c
docker pull container-registry.oracle.com/database/enterprise:19.3.0.0
```

**2. PostgreSQL**
```bash
# PostgreSQL 16
docker pull postgres:16-alpine
```

**3. MongoDB**
```bash
# MongoDB 7
docker pull mongo:7
```

**4. Redis (Optional)**
```bash
# Redis 7
docker pull redis:7-alpine
```

---

## 🔧 Installation Steps

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd AI_FRAUD_DETECTION
```

### 2. Setup Environment Variables
```bash
# Copy example env file
cp .env.example .env

# Edit .env file
nano .env
```

**Required Environment Variables:**
```bash
# Database Connections
ORACLE_URI=oracle+oracledb://system:password@localhost:1521/XE
POSTGRES_URI=postgresql://postgres:password@localhost:5432/frauddb
MONGO_URI=mongodb://root:password@localhost:27017/

# API Configuration
API_SECRET_KEY=your-secret-key-here-change-this
API_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Install Backend Dependencies
```bash
cd services/api

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies
```bash
cd ../../apps/web

# Install Node packages
npm install

# Or use yarn
yarn install
```

### 5. Start Databases
```bash
cd ../../

# Start all databases with Docker Compose
docker-compose -f infra/docker/docker-compose.yml up -d

# Wait for databases to be ready (30-60 seconds)
docker-compose -f infra/docker/docker-compose.yml ps
```

### 6. Initialize Databases
```bash
# Run initialization scripts
make init-db

# Or manually:
docker exec -i oracle-db sqlplus system/password@XE @/docker-entrypoint-initdb.d/schema.sql
docker exec -i postgres-db psql -U postgres -d frauddb -f /docker-entrypoint-initdb.d/schema.sql
docker exec -i mongo-db mongosh -u root -p password --authenticationDatabase admin /docker-entrypoint-initdb.d/init.js
```

### 7. Seed Test Data (Optional)
```bash
# Seed databases with sample fraud data
make seed

# Or manually:
python tools/fake_data.py
```

---

## ▶️ Running the Application

### Method 1: Using Make (Recommended)
```bash
# Start everything
make run

# Or start individually:
make run-api      # Start backend API
make run-web      # Start frontend
make run-worker   # Start background worker
```

### Method 2: Manual Start

**Terminal 1 - Backend API:**
```bash
cd services/api
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd apps/web
npm run dev
```

**Terminal 3 - Databases (if not using Docker):**
```bash
docker-compose -f infra/docker/docker-compose.yml up
```

### Method 3: Docker Compose (All-in-One)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

---

## 🌐 Accessing the Application

Once running, access:

- **Frontend:** http://localhost:3000
- **API Documentation:** http://localhost:8000/docs
- **API Health Check:** http://localhost:8000/health

**Default Login:**
- Username: `demo`
- Password: (auto-login enabled for demo)

---

## 📱 Available Pages

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/dashboard` | Main fraud alerts dashboard |
| Analytics | `/dashboard-enhanced` | Enhanced analytics with charts |
| ML Model | `/ml-model` | Machine learning predictions |
| Network Graph | `/network-graph` | Fraud ring visualization |
| Fraud Map | `/fraud-map` | Geographic fraud mapping |
| Cases | `/cases` | Case management |
| Investigations | `/investigation` | Investigation workspace |
| User Management | `/rbac` | RBAC user management |
| CRUD Monitor | `/crud-monitor` | Database operations monitor |

---

## 🔧 Configuration

### Frontend Configuration

**`apps/web/next.config.js`:**
```javascript
module.exports = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  // ... other config
}
```

### Backend Configuration

**`services/api/config.py`:**
```python
class Settings(BaseSettings):
    oracle_uri: str
    postgres_uri: str
    mongo_uri: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
```

### Database Ports

- **Oracle:** 1521
- **PostgreSQL:** 5432
- **MongoDB:** 27017
- **Redis:** 6379

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

#### 2. Database Connection Failed
```bash
# Check if databases are running
docker-compose ps

# Restart databases
docker-compose restart oracle-db postgres-db mongo-db

# Check logs
docker-compose logs oracle-db
```

#### 3. Node Modules Issues
```bash
cd apps/web
rm -rf node_modules package-lock.json
npm install
```

#### 4. Python Dependencies Issues
```bash
cd services/api
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

#### 5. Oracle Connection Error
```bash
# Make sure Oracle Instant Client is installed
# Download from: https://www.oracle.com/database/technologies/instant-client/downloads.html

# On macOS
brew install oracle-instantclient

# On Linux
sudo apt install libaio1
```

#### 6. Too Many Open Files (macOS)
```bash
# Increase file limit
ulimit -n 65536

# Or add to ~/.zshrc or ~/.bashrc:
echo "ulimit -n 65536" >> ~/.zshrc
```

---

## 🧪 Testing

### Backend Tests
```bash
cd services/api
pytest tests/
```

### Frontend Tests
```bash
cd apps/web
npm test
```

### API Health Check
```bash
curl http://localhost:8000/health
```

---

## 📦 Production Deployment

### Build Frontend
```bash
cd apps/web
npm run build
npm start
```

### Production Environment Variables
```bash
# Set production URLs
NEXT_PUBLIC_API_URL=https://your-api-domain.com
API_SECRET_KEY=strong-random-secret-key

# Use production databases
ORACLE_URI=oracle://user:pass@prod-oracle:1521/service
POSTGRES_URI=postgresql://user:pass@prod-postgres:5432/frauddb
MONGO_URI=mongodb://user:pass@prod-mongo:27017/
```

---

## 🔒 Security Checklist

Before production deployment:

- [ ] Change all default passwords
- [ ] Update `API_SECRET_KEY` to a strong random value
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Enable database authentication
- [ ] Set up backup and recovery
- [ ] Enable audit logging
- [ ] Configure CORS properly
- [ ] Implement rate limiting
- [ ] Set up monitoring and alerts

---

## 📚 Additional Resources

- [API Documentation](docs/API.md)
- [Architecture Overview](docs/ARCH.md)
- [Production Checklist](docs/PRODUCTION_CHECKLIST.md)
- [Feature Documentation](WORLD_CLASS_FEATURES_COMPLETE.md)

---

## 💬 Support

For questions or issues:
1. Check the troubleshooting section
2. Review logs: `docker-compose logs -f`
3. Contact the development team

---

**Last Updated:** October 29, 2025

