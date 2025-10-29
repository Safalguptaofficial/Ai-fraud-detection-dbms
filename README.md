# 🛡️ FraudGuard - AI-Powered Fraud Detection System

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](VERSION.md)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

**World-class, enterprise-grade fraud detection platform** with advanced machine learning, network analysis, and collaborative investigation tools.

---

## 🌟 Features

### Core Capabilities
- ✅ **Real-time Fraud Detection** - ML-powered risk scoring
- ✅ **Network Graph Visualization** - Fraud ring identification
- ✅ **Explainable AI** - Feature importance & triggered rules
- ✅ **RBAC System** - 4 roles with granular permissions
- ✅ **Investigation Workspace** - Timeline, evidence, collaboration
- ✅ **Professional Reporting** - PDF & CSV exports
- ✅ **Dark Mode** - Full theme support
- ✅ **Mobile Responsive** - Works on all devices

### Advanced Features
- 🧠 **Ensemble ML Model** - Isolation Forest + Rules + Velocity
- 🕸️ **Network Graph** - Visual fraud ring detection
- 🗺️ **Geographic Map** - Location-based fraud analysis
- 📊 **Enhanced Analytics** - Interactive charts & trends
- 🔍 **Smart Filtering** - Search, severity, date range
- ⚡ **Bulk Actions** - Approve, reject, export multiple alerts
- 💬 **AI Chatbot** - Natural language fraud queries
- ⌨️ **Keyboard Shortcuts** - Quick navigation (Cmd+K)

---

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ ([Download](https://nodejs.org/))
- **Python** 3.11+ ([Download](https://www.python.org/))
- **Docker & Docker Compose** ([Download](https://www.docker.com/))

### Installation

```bash
# 1. Clone repository
git clone <your-repo-url>
cd AI_FRAUD_DETECTION

# 2. Setup environment
cp .env.example .env
# Edit .env with your database credentials

# 3. Install dependencies
cd apps/web && npm install
cd ../../services/api && pip install -r requirements.txt

# 4. Start databases
docker-compose -f infra/docker/docker-compose.yml up -d

# 5. Run application
make run
```

**Access:** http://localhost:3000

📖 **Full Installation Guide:** [INSTALLATION.md](INSTALLATION.md)

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                     │
│  Dashboard | ML Model | Network Graph | Investigation       │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│  Routes | ML Model | RBAC | Risk Scoring | Auth            │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼────┐  ┌──────▼──────┐  ┌────▼─────┐
│   Oracle    │  │ PostgreSQL  │  │ MongoDB  │
│ Transactions│  │  Analytics  │  │  Cases   │
└─────────────┘  └─────────────┘  └──────────┘
```

---

## 🎯 Key Components

### Frontend (`apps/web/`)
- **Next.js 14** - React framework
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization
- **React Leaflet** - Maps
- **TypeScript** - Type safety

### Backend (`services/api/`)
- **FastAPI** - Python web framework
- **Pydantic** - Data validation
- **NumPy** - ML computations
- **oracledb, psycopg2, pymongo** - Database drivers

### Databases
- **Oracle** - Transaction data (OLTP)
- **PostgreSQL** - Analytics & anomalies (OLAP)
- **MongoDB** - Case management (NoSQL)

---

## 📱 Application Pages

| Page | URL | Description |
|------|-----|-------------|
| 🏠 Dashboard | `/dashboard` | Main alerts view with filters & bulk actions |
| 📈 Analytics | `/dashboard-enhanced` | Charts, trends, heatmaps |
| 🧠 ML Model | `/ml-model` | Real-time fraud predictions |
| 🕸️ Network Graph | `/network-graph` | Fraud ring visualization |
| 🗺️ Fraud Map | `/fraud-map` | Geographic analysis |
| 📁 Cases | `/cases` | Case management CRUD |
| 🔍 Investigations | `/investigation` | Timeline, evidence, notes |
| 👥 Users | `/rbac` | User management & permissions |
| 💾 Monitor | `/crud-monitor` | Database operations log |

---

## 🔐 User Roles (RBAC)

| Role | Permissions | Use Case |
|------|-------------|----------|
| **ADMIN** | Full access | System administrators |
| **MANAGER** | Approve, manage team | Fraud team leads |
| **ANALYST** | Review alerts, create cases | Fraud analysts |
| **VIEWER** | Read-only access | Compliance, auditors |

---

## 🧠 ML Model Details

### Ensemble Architecture
```
Prediction = 40% Isolation Forest
           + 30% Rule-Based System  
           + 30% Velocity Model
```

### Features Analyzed
1. **Transaction Amount** - Size and deviation
2. **Velocity** - Transactions per hour
3. **Time Patterns** - Time since last transaction
4. **Location** - Geographic anomalies
5. **Merchant Risk** - Merchant reputation
6. **Device/IP** - Device and IP changes
7. **Temporal** - Hour of day, weekend patterns

### Output
- **Risk Score:** 0-100
- **Risk Level:** LOW / MEDIUM / HIGH
- **Confidence:** Model agreement percentage
- **Triggered Rules:** Which rules fired
- **Feature Contributions:** What drove the score
- **Recommendation:** Action to take

---

## 📦 Software Requirements

### Development
- Node.js 18+ & npm 9+
- Python 3.11+ & pip
- Docker & Docker Compose
- Git

### Production
- Oracle 11g+ (or Oracle XE)
- PostgreSQL 12+
- MongoDB 4.4+
- Redis 6+ (optional, for caching)
- 4+ CPU cores, 8+ GB RAM

### Dependencies

**Backend:**
```
fastapi, uvicorn, pydantic
oracledb, psycopg2-binary, pymongo
numpy, pandas
python-jose, passlib
prometheus-client
```

**Frontend:**
```
next, react, typescript
tailwindcss, lucide-react
recharts, react-leaflet
@tanstack/react-query, sonner
```

📖 **Full List:** [INSTALLATION.md](INSTALLATION.md#software--library-requirements)

---

## 🔧 Configuration

### Environment Variables (`.env`)
```bash
# Database Connections
ORACLE_URI=oracle+oracledb://system:password@localhost:1521/XE
POSTGRES_URI=postgresql://postgres:password@localhost:5432/frauddb
MONGO_URI=mongodb://root:password@localhost:27017/

# API Configuration
API_SECRET_KEY=your-secret-key-change-this
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🎨 Screenshots

### Dashboard with Bulk Actions
![Dashboard](docs/screenshots/dashboard.png)

### ML Model Predictions
![ML Model](docs/screenshots/ml-model.png)

### Network Graph
![Network Graph](docs/screenshots/network-graph.png)

### Investigation Workspace
![Investigation](docs/screenshots/investigation.png)

---

## 📚 Documentation

- 📖 [Installation Guide](INSTALLATION.md) - Complete setup instructions
- 📊 [API Documentation](docs/API.md) - REST API reference
- 🏗️ [Architecture](docs/ARCH.md) - System design & patterns
- ✅ [Production Checklist](docs/PRODUCTION_CHECKLIST.md) - Deployment guide
- 🎯 [Feature Guide](WORLD_CLASS_FEATURES_COMPLETE.md) - Feature documentation
- 📝 [Version History](VERSION.md) - Changelog & releases

---

## 🧪 Testing

### Run Backend Tests
```bash
cd services/api
pytest tests/ -v
```

### Run Frontend Tests
```bash
cd apps/web
npm test
```

### API Health Check
```bash
curl http://localhost:8000/health
```

---

## 🚢 Deployment

### Development
```bash
make run
```

### Production
```bash
# Build frontend
cd apps/web && npm run build

# Start with PM2
pm2 start ecosystem.config.js

# Or use Docker
docker-compose -f docker-compose.prod.yml up -d
```

📖 **Production Guide:** [docs/PRODUCTION_CHECKLIST.md](docs/PRODUCTION_CHECKLIST.md)

---

## 🔒 Security Features

- ✅ JWT authentication
- ✅ Role-based access control (RBAC)
- ✅ Password hashing (bcrypt)
- ✅ SQL injection prevention
- ✅ CORS configuration
- ✅ Rate limiting
- ✅ Audit logging
- ✅ Session management

---

## 🌐 Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

---

## 📊 Performance

- **API Response Time:** < 100ms (avg)
- **Dashboard Load:** < 2s
- **ML Prediction:** < 50ms
- **Concurrent Users:** 100+ supported
- **Database Queries:** Optimized with indexes

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 License

Proprietary - Internal Use Only

---

## 👥 Team

- **Development:** AI Development Team
- **Design:** UX/UI Design Team
- **Domain Experts:** Fraud Detection Specialists

---

## 📞 Support

For questions, issues, or feature requests:
- 📧 Email: fraud-support@company.com
- 💬 Slack: #fraud-detection
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/fraud-detection/issues)

---

## 🎉 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Recharts](https://recharts.org/)
- [Leaflet](https://leafletjs.com/)

---

## 📈 Roadmap

### v2.1.0 (Next Quarter)
- [ ] Real-time WebSocket updates
- [ ] Advanced ML model training interface
- [ ] Customizable dashboards
- [ ] Multi-factor authentication (MFA)
- [ ] Email/SMS notifications

### v3.0.0 (Future)
- [ ] Blockchain transaction monitoring
- [ ] Voice commands & natural language
- [ ] AR/VR fraud visualization
- [ ] Advanced graph analytics
- [ ] Multi-tenant support

---

## ⭐ Star History

If you find this project useful, please consider giving it a star!

---

**Made with ❤️ by the FraudGuard Team**

**Last Updated:** October 29, 2025 | **Version:** 2.0.0
