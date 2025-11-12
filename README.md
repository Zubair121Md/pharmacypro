# 🏥 Pharmacy Revenue Management System

A comprehensive full-stack application for managing pharmacy revenue, doctor allocations, and sales analytics with advanced ID-based matching and flexible data processing, designed to operate offline after initial setup.

## 🎯 Overview

The Pharmacy Revenue Management System processes pharmacy invoice data with flexible column mapping, matches invoices with master data using a deterministic ID generation algorithm, and generates comprehensive revenue analytics and visualizations.

### Key Features
- **ID Generation**: Creates unique Pharmacy_IDs (e.g., "GM-CAL-001") from pharmacy names
- **Flexible Mapping**: Handles various Excel column name variations
- **Revenue Analytics**: Comprehensive dashboards with role-based access
- **Offline Operation**: All dependencies bundled locally
- **Role-Based Access**: Super Admin, Admin, User permissions
- **Data Export**: Excel, CSV, PDF with data masking
- **Product Revenue Analytics**: Detailed product-wise revenue tracking
- **Real-time Processing**: Advanced file processing with unmatched record management

## 📸 Application Screenshots

### 🏠 Dashboard Overview
![Dashboard](https://github.com/Zubair121Md/pharmacy-revenue-app/raw/master/screenshots/dashboard.png)
*Main dashboard showing total revenue, pharmacies, doctors, and growth metrics with interactive charts*

### 📊 Analytics Dashboard
![Analytics](https://github.com/Zubair121Md/pharmacy-revenue-app/raw/master/screenshots/analytics.png)
*Comprehensive analytics with revenue breakdowns by pharmacy, doctor, rep, HQ, area, and product*

### 📁 File Upload Interface
![File Upload](https://github.com/Zubair121Md/pharmacy-revenue-app/raw/master/screenshots/file-upload.png)
*Drag-and-drop file upload interface for invoice files and master mapping data*

### ⚠️ Unmatched Records Management
![Unmatched Records](https://github.com/Zubair121Md/pharmacy-revenue-app/raw/master/screenshots/unmatched-records.png)
*Management interface for reviewing and handling unmatched pharmacy records*

### 📈 Recent Uploads
![Recent Uploads](https://github.com/Zubair121Md/pharmacy-revenue-app/raw/master/screenshots/recent-uploads.png)
*Recent file processing history with detailed metrics and export options*

### 👥 Admin Panel
![Admin Panel](https://github.com/Zubair121Md/pharmacy-revenue-app/raw/master/screenshots/admin-panel.png)
*Administrative interface for user management, system settings, and monitoring*

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (SQLite)      │
│   Port: 3000    │    │   Port: 8000    │    │   Local File    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Tauri App     │    │   Redis Cache   │    │   File Storage  │
│   (Desktop)     │    │   (Optional)    │    │   (Excel/CSV)   │
│   Cross-Platform│    │   Port: 6379    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- SQLite3
- Git

### Installation

1. **Clone the repository**:
```bash
git clone git@github.com:Zubair121Md/pharmacy-revenue-app.git
cd pharmacy-revenue-app
```

2. **Backend Setup**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main_complete:app --host 127.0.0.1 --port 8000 --reload
```

3. **Frontend Setup**:
```bash
cd frontend
npm install
npm start
```

4. **Tauri Desktop App** (Optional):
```bash
npm run tauri dev
```

### Default Login Credentials
- **Super Admin**: admin / admin123
- **Admin**: manager / manager123
- **User**: user / user123

## 📊 Sample Data

### Master Data Format
```
REP_Names | Doctor_Names | Doctor_ID | Pharmacy_Names | Pharmacy_ID | Product_Names | Product_ID | Product_Price | HQ | AREA
VIKRAM    | DR SHAJIKUMAR | DR_SHA_733| Gayathri Medicals | GM_CAL_001 | ENDOL 650 | PRD_6824 | 13.46 | CL | CALICUT
```

### Invoice Data Format
```
Pharmacy_Name | Product | Quantity | Amount
Gayathri Medicals | ENDOL 650 | 20 | 269.2
```

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=sqlite:///./pharmacy_revenue.db

# JWT
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

## 📁 Project Structure

```
pharmacy-revenue-app/
├── frontend/                 # React application
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API services
│   │   ├── store/           # Redux store
│   │   └── utils/           # Utility functions
│   └── package.json
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── main_complete.py  # Main application
│   │   ├── tasks_enhanced.py # Background tasks
│   │   └── models/          # Data models
│   ├── requirements.txt
│   └── pharmacy_revenue.db   # SQLite database
├── src-tauri/               # Tauri desktop app
├── screenshots/             # Application screenshots
└── README.md                # This file
```

## 🛠️ Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main_complete:app --reload --host 127.0.0.1 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### Tauri Desktop Development
```bash
npm run tauri dev
```

## 📊 Features Overview

### 🎯 Core Features
- **Multi-format File Processing**: Excel (.xlsx, .xls), CSV support
- **Intelligent ID Generation**: Automatic pharmacy ID creation from names
- **Flexible Column Mapping**: Handles various column name variations
- **Real-time Analytics**: Live revenue tracking and reporting
- **Role-based Access Control**: Super Admin, Admin, User roles
- **Data Export**: Excel, CSV export with customizable formats

### 📈 Analytics Capabilities
- **Revenue by Pharmacy**: Top performing pharmacies
- **Revenue by Doctor**: Doctor-wise revenue analysis
- **Revenue by Representative**: Sales rep performance
- **Revenue by HQ**: Headquarters-wise breakdown
- **Revenue by Area**: Geographic revenue analysis
- **Revenue by Product**: Product-wise sales tracking
- **Data Distribution**: Statistical analysis
- **PERI Analysis**: Performance evaluation metrics

### 🔧 Technical Features
- **Offline Operation**: Works without internet after setup
- **Cross-platform**: Web and desktop applications
- **Real-time Processing**: Background task processing
- **Error Handling**: Comprehensive error management
- **Data Validation**: Input validation and sanitization
- **Caching**: Redis-based caching for performance

## 🚀 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Get current user

### Analytics
- `GET /api/v1/analytics/revenue-by-pharmacy` - Pharmacy revenue
- `GET /api/v1/analytics/revenue-by-doctor` - Doctor revenue
- `GET /api/v1/analytics/revenue-by-rep` - Representative revenue
- `GET /api/v1/analytics/revenue-by-hq` - HQ revenue
- `GET /api/v1/analytics/revenue-by-area` - Area revenue
- `GET /api/v1/analytics/revenue-by-product` - Product revenue
- `GET /api/v1/analytics/data-distribution` - Data distribution
- `GET /api/v1/analytics/peri` - PERI analysis

### File Management
- `POST /api/v1/files/upload` - Upload files
- `GET /api/v1/files/recent` - Recent uploads
- `GET /api/v1/files/unmatched` - Unmatched records
- `POST /api/v1/files/process` - Process files

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**:
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

2. **Database Issues**:
```bash
# Reset database
rm backend/pharmacy_revenue.db
# Restart backend to recreate
```

3. **Node Modules Issues**:
```bash
# Clear npm cache
npm cache clean --force
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

## 📞 Support

For technical support:
1. Check the troubleshooting section above
2. Review logs in the browser console
3. Check backend logs in terminal
4. Create an issue on GitHub

## 📄 License

This project is proprietary software. All rights reserved.

---

**Version**: 2.1  
**Last Updated**: January 2025  
**Repository**: [Zubair121Md/pharmacy-revenue-app](https://github.com/Zubair121Md/pharmacy-revenue-app)