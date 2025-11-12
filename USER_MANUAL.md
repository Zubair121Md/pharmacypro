# Pharmacy Revenue Management System - User Manual

## 📖 Table of Contents

1. [Getting Started](#getting-started)
2. [User Interface](#user-interface)
3. [File Upload](#file-upload)
4. [Analytics & Reporting](#analytics--reporting)
5. [User Management](#user-management)
6. [System Administration](#system-administration)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

## Getting Started

### System Overview

The Pharmacy Revenue Management System is a comprehensive solution for managing pharmacy revenue data, generating analytics, and creating reports. The system processes Excel files containing pharmacy information and generates unique IDs for revenue tracking and analysis.

### Key Features

- **File Upload & Processing**: Upload Excel files with pharmacy data
- **ID Generation**: Automatic generation of unique pharmacy IDs
- **Data Matching**: Match invoice data with master pharmacy records
- **Analytics Dashboard**: Comprehensive revenue analytics and reporting
- **User Management**: Role-based access control
- **Data Export**: Export data in multiple formats (Excel, CSV, PDF)
- **ML Integration**: AI-powered pharmacy matching
- **Audit Logging**: Complete audit trail of all activities

### User Roles

#### User
- Upload and process files
- View analytics and reports
- Export data
- Manage unmatched records

#### Admin
- All User permissions
- Manage other users
- View audit logs
- Access advanced features
- System monitoring

#### Super Admin
- All Admin permissions
- System configuration
- Backup management
- Full system access

## User Interface

### Login Page

1. Navigate to the application URL
2. Enter your username and password
3. Click "Login"
4. You'll be redirected to the dashboard

### Dashboard

The dashboard provides an overview of:
- Total revenue
- Number of invoices processed
- Active pharmacies
- Recent activities
- Performance metrics

### Navigation

- **Dashboard**: Overview and summary metrics
- **File Upload**: Upload and process Excel files
- **Analytics**: Revenue analytics and reporting
- **Admin Panel**: User management (Admin/Super Admin only)
- **Settings**: User preferences and system settings
- **Unmatched Records**: Manage unmatched pharmacy records

## File Upload

### Supported File Formats

- Excel (.xlsx)
- CSV (.csv)

### Master Data File

Required columns:
- `REP_Names`: Sales representative names
- `Doctor_Names`: Doctor names
- `Doctor_ID`: Unique doctor identifiers
- `Pharmacy_Names`: Pharmacy names
- `Pharmacy_ID`: Unique pharmacy identifiers
- `Product_Names`: Product names
- `Product_ID`: Unique product identifiers
- `Product_Price`: Product prices
- `HQ`: Headquarters location
- `AREA`: Geographic area

### Invoice Data File

Required columns:
- `Pharmacy Name`: Pharmacy name (with location, e.g., "Gayathri Medicals,Calicut")
- `Product`: Product name
- `Quantity`: Quantity sold
- `Amount`: Total amount

### Upload Process

1. Navigate to "File Upload"
2. Select file type (Master Data or Invoice Data)
3. Drag and drop your file or click to browse
4. Wait for processing to complete
5. Review results and any unmatched records

### Data Quality Checks

The system performs several quality checks:
- Column name validation
- Data type validation
- Required field validation
- Duplicate detection
- Format validation

## Analytics & Reporting

### Dashboard Analytics

#### Summary Metrics
- Total Revenue: Sum of all processed amounts
- Total Invoices: Number of invoices processed
- Active Pharmacies: Number of unique pharmacies
- Average Order Value: Revenue per invoice
- Growth Rate: Period-over-period growth

#### Revenue Analytics
- **By Pharmacy**: Revenue breakdown by pharmacy
- **By Doctor**: Revenue breakdown by doctor
- **By Rep**: Revenue breakdown by sales representative
- **By Area**: Revenue breakdown by geographic area

#### Monthly Trends
- Revenue trends over time
- Month-over-month comparisons
- Seasonal analysis
- Growth projections

#### Top Performers
- Top pharmacies by revenue
- Top doctors by revenue
- Top products by sales
- Performance rankings

### Custom Reports

#### Available Report Types
1. **Comprehensive Report**: Complete analysis with all metrics
2. **Executive Summary**: High-level overview for management
3. **Pharmacy Performance**: Detailed pharmacy analysis
4. **Monthly Trends**: Revenue trends and forecasting

#### Export Formats
- Excel (.xlsx): Multi-sheet reports with charts
- CSV (.csv): Raw data for further analysis
- PDF (.pdf): Formatted reports for presentation

#### Report Generation
1. Navigate to "Analytics"
2. Select report type
3. Choose date range
4. Select export format
5. Click "Generate Report"

### Data Filtering

- **Date Range**: Filter by specific date ranges
- **Pharmacy**: Filter by specific pharmacies
- **Product**: Filter by specific products
- **Area**: Filter by geographic areas
- **Rep**: Filter by sales representatives

## User Management

### Creating Users (Admin/Super Admin)

1. Navigate to "Admin Panel" > "User Management"
2. Click "Add New User"
3. Fill in user details:
   - Username
   - Email
   - Password
   - Role (User/Admin/Super Admin)
   - Area (Geographic assignment)
4. Click "Create User"

### Managing Users

#### Edit User
1. Click on user in the user list
2. Modify user details
3. Click "Save Changes"

#### Deactivate User
1. Select user
2. Click "Deactivate"
3. Confirm action

#### Reset Password
1. Select user
2. Click "Reset Password"
3. New password will be generated and displayed

### User Permissions

#### User Role Permissions
- **View Data**: Access to analytics and reports
- **Upload Files**: Upload and process files
- **Export Data**: Export reports and data
- **Manage Unmatched**: Handle unmatched records

#### Admin Role Permissions
- All User permissions
- **Manage Users**: Create, edit, deactivate users
- **View Audit Logs**: Access system audit trail
- **System Monitoring**: View system statistics

#### Super Admin Permissions
- All Admin permissions
- **System Configuration**: Modify system settings
- **Backup Management**: Create and restore backups
- **Full Access**: Complete system access

## System Administration

### Audit Logs

View all system activities:
1. Navigate to "Admin Panel" > "Audit Logs"
2. Filter by:
   - User
   - Action type
   - Date range
   - Severity level
3. Export logs if needed

### System Statistics

Monitor system performance:
- Active users
- Files processed
- Database size
- System health
- Error rates

### Backup Management

#### Create Backup
1. Navigate to "Admin Panel" > "Backup Management"
2. Click "Create Backup"
3. Wait for completion
4. Download backup file

#### Restore Backup
1. Upload backup file
2. Click "Restore"
3. Confirm restoration
4. Wait for completion

### System Settings

Configure system parameters:
- File upload limits
- Data retention policies
- Email notifications
- Security settings
- Performance tuning

## Troubleshooting

### Common Issues

#### File Upload Fails

**Problem**: File upload returns error
**Solutions**:
1. Check file format (must be .xlsx or .csv)
2. Verify required columns are present
3. Ensure file size is under 10MB
4. Check file is not corrupted

#### Analytics Not Loading

**Problem**: Dashboard shows no data
**Solutions**:
1. Ensure data has been uploaded
2. Check date range filters
3. Verify user permissions
4. Refresh the page

#### Login Issues

**Problem**: Cannot log in
**Solutions**:
1. Verify username and password
2. Check if account is active
3. Contact administrator if locked
4. Clear browser cache

#### Performance Issues

**Problem**: System is slow
**Solutions**:
1. Check internet connection
2. Close other browser tabs
3. Clear browser cache
4. Contact administrator

### Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| AUTH_001 | Invalid credentials | Check username/password |
| AUTH_002 | Account locked | Contact administrator |
| FILE_001 | Invalid file format | Use .xlsx or .csv |
| FILE_002 | File too large | Reduce file size |
| DB_001 | Database error | Contact administrator |
| PERM_001 | Insufficient permissions | Contact administrator |

### Getting Help

#### Self-Service
1. Check this user manual
2. Review FAQ section
3. Check system status page

#### Contact Support
- **Email**: support@pharmacy-revenue.com
- **Phone**: +1-800-PHARMACY
- **Hours**: Monday-Friday, 9 AM - 6 PM EST

#### Report Issues
1. Navigate to "Settings" > "Report Issue"
2. Describe the problem
3. Attach screenshots if helpful
4. Submit the report

## FAQ

### General Questions

**Q: What file formats are supported?**
A: The system supports Excel (.xlsx) and CSV (.csv) files.

**Q: What is the maximum file size?**
A: The maximum file size is 10MB per file.

**Q: How many records can I process?**
A: The system can handle up to 50,000 records per file.

**Q: Is my data secure?**
A: Yes, all data is encrypted and stored securely with role-based access control.

### Technical Questions

**Q: How does ID generation work?**
A: The system uses a deterministic algorithm to generate unique IDs based on pharmacy name and location.

**Q: What happens to unmatched records?**
A: Unmatched records are stored for manual review and mapping by administrators.

**Q: Can I export my data?**
A: Yes, you can export data in Excel, CSV, and PDF formats.

**Q: How often is data backed up?**
A: The system performs daily automated backups with 30-day retention.

### User Management

**Q: How do I change my password?**
A: Go to Settings > User Profile > Change Password.

**Q: Can I have multiple user accounts?**
A: No, each user should have only one account. Contact your administrator for access changes.

**Q: What if I forget my password?**
A: Contact your system administrator to reset your password.

**Q: Can I access the system from multiple devices?**
A: Yes, you can access the system from any device with internet connectivity.

### Data and Analytics

**Q: How accurate are the analytics?**
A: Analytics are based on the data you upload and are updated in real-time.

**Q: Can I customize reports?**
A: Yes, you can filter data by date range, pharmacy, product, and other criteria.

**Q: How long is data retained?**
A: Data is retained for 3 years by default, with archiving for older data.

**Q: Can I import data from other systems?**
A: Currently, only Excel and CSV files are supported. Contact support for other formats.

---

*This user manual is regularly updated. For the latest version, visit the system documentation page.*
