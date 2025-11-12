# 🏥 Pharmacy Revenue Management System - DEPLOYMENT GUIDE

## 🚀 QUICK DEPLOYMENT

### For End Users (Recommended)
1. **Download** the `Pharmacy_Revenue_Management_DEPLOYED_v1.0.4.zip`
2. **Extract** to your desired location
3. **Run**: `./start_tauri_app.sh`
4. **Wait** for services to start (30-60 seconds)
5. **Desktop app** opens automatically

### For Developers
1. **Clone** the repository
2. **Install dependencies**:
   ```bash
   # Backend
   cd backend && pip install -r requirements.txt
   
   # Frontend
   cd frontend && npm install
   
   # Tauri
   cd src-tauri && npm install
   ```
3. **Run**: `./start_tauri_app.sh`

## 📋 SYSTEM REQUIREMENTS

### Minimum Requirements
- **macOS**: 10.15+ (Catalina or later)
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 500MB for installation
- **Python**: 3.8+ (auto-installed by script)
- **Node.js**: 16+ (auto-installed by script)
- **Rust**: Latest stable (for development only)

### Recommended Requirements
- **macOS**: 12+ (Monterey or later)
- **RAM**: 8GB or more
- **Disk Space**: 1GB for full development environment
- **Internet**: Required for initial dependency installation

## 🔧 DEPLOYMENT OPTIONS

### Option 1: Desktop App (End Users)
- **File**: `Pharmacy Revenue Management.app`
- **Installer**: `Pharmacy Revenue Management_1.0.0_aarch64.dmg`
- **Startup**: `./start_tauri_app.sh`
- **Best for**: End users who want a desktop application

### Option 2: Web Application (Developers)
- **Backend**: `http://127.0.0.1:8000`
- **Frontend**: `http://127.0.0.1:3000`
- **API Docs**: `http://127.0.0.1:8000/docs`
- **Best for**: Developers and web-based usage

### Option 3: Production Deployment
- **Docker**: Use provided Dockerfiles
- **Cloud**: Deploy to AWS, GCP, or Azure
- **Best for**: Production environments

## 🎯 FEATURES DEPLOYED

### ✅ Core Features
- **File Upload**: Excel files with unlimited rows
- **Data Processing**: ID generation, matching, ML fallback
- **Analytics**: Revenue by pharmacy, doctor, area
- **Export**: CSV, Excel exports
- **User Management**: Authentication and roles
- **Real-time Processing**: Live updates and status

### ✅ Technical Features
- **No Row Limits**: Processes unlimited files
- **Enhanced Processing**: Advanced algorithms
- **Error Handling**: Comprehensive error management
- **Performance**: Optimized for large datasets
- **Security**: JWT authentication and role-based access

## 🔧 TROUBLESHOOTING

### Common Issues

#### "Services Not Available" Error
- **Cause**: Backend or frontend not running
- **Solution**: Run `./start_tauri_app.sh` and wait for "Both services are ready!"

#### "Python not found" Error
- **Cause**: Python not installed
- **Solution**: Install Python 3.8+ from python.org

#### "Node.js not found" Error
- **Cause**: Node.js not installed
- **Solution**: Install Node.js 16+ from nodejs.org

#### App Crashes on Startup
- **Cause**: Missing dependencies or port conflicts
- **Solution**: 
  1. Kill existing processes: `pkill -f "uvicorn\|react-scripts\|tauri"`
  2. Restart: `./start_tauri_app.sh`

#### File Upload Limited to 100 Rows
- **Status**: FIXED - No more row limits
- **Solution**: Update to latest version

### Performance Issues

#### Slow File Processing
- **Cause**: Large files or insufficient RAM
- **Solution**: 
  - Close other applications
  - Use files with < 50,000 rows for optimal performance
  - Ensure 8GB+ RAM available

#### App Freezes During Upload
- **Cause**: Memory issues or corrupted data
- **Solution**:
  - Restart the application
  - Check file format (must be .xlsx or .xls)
  - Verify data integrity

## 📊 MONITORING & LOGS

### Service Status
- **Backend**: `http://127.0.0.1:8000/docs`
- **Frontend**: `http://127.0.0.1:3000`
- **Health Check**: `http://127.0.0.1:8000/api/v1/health`

### Log Files
- **Backend Logs**: Check terminal output
- **Frontend Logs**: Check browser console
- **Tauri Logs**: Check terminal output

### Performance Metrics
- **File Processing**: ~1000 rows/second
- **Memory Usage**: ~500MB base + 50MB per 10K rows
- **Startup Time**: 30-60 seconds

## 🚀 PRODUCTION DEPLOYMENT

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build individual services
docker build -t pharmacy-backend ./backend
docker build -t pharmacy-frontend ./frontend
```

### Cloud Deployment
1. **Backend**: Deploy to cloud service (AWS Lambda, Google Cloud Functions)
2. **Frontend**: Deploy to CDN (AWS CloudFront, Netlify)
3. **Database**: Use managed database service
4. **Storage**: Use cloud storage for file uploads

### Security Considerations
- **HTTPS**: Enable SSL/TLS certificates
- **Authentication**: Implement proper user management
- **Data Encryption**: Encrypt sensitive data
- **Access Control**: Implement proper role-based access
- **Audit Logging**: Log all user actions

## 📞 SUPPORT

### Getting Help
1. **Check logs** for error messages
2. **Verify requirements** are met
3. **Restart services** using startup script
4. **Contact support** with error details

### Reporting Issues
- **Include**: Error messages, system info, steps to reproduce
- **Attach**: Log files and screenshots
- **Specify**: Operating system and version

### Updates
- **Check**: For new versions regularly
- **Backup**: Data before updating
- **Test**: In development environment first

## 🎉 SUCCESS INDICATORS

### ✅ Deployment Successful When:
- Backend responds at `http://127.0.0.1:8000/docs`
- Frontend loads at `http://127.0.0.1:3000`
- Tauri app opens and shows full interface
- File upload works with unlimited rows
- All analytics and charts display properly
- Export functions work correctly
- No error messages in console

### 🚀 Ready for Production When:
- All tests pass
- Performance meets requirements
- Security measures implemented
- Monitoring and logging configured
- Backup and recovery procedures in place
- Documentation updated
- User training completed
