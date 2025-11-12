"""
Audit Logging System for Pharmacy Revenue Management System
Version: 2.0
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from enum import Enum
import uuid

from app.database import AuditLog, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuditAction(Enum):
    """Audit action types"""
    LOGIN = "login"
    LOGOUT = "logout"
    FILE_UPLOAD = "file_upload"
    FILE_PROCESS = "file_process"
    DATA_EXPORT = "data_export"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    PHARMACY_MAP = "pharmacy_map"
    PHARMACY_UNMAP = "pharmacy_unmap"
    SETTINGS_UPDATE = "settings_update"
    REPORT_GENERATE = "report_generate"
    SYSTEM_BACKUP = "system_backup"
    DATA_DELETE = "data_delete"
    PERMISSION_CHANGE = "permission_change"

class AuditSeverity(Enum):
    """Audit severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuditLogger:
    """Comprehensive audit logging system"""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger('audit')
        
        # Setup audit logger
        audit_handler = logging.FileHandler('audit.log')
        audit_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        audit_handler.setFormatter(audit_formatter)
        self.logger.addHandler(audit_handler)
        self.logger.setLevel(logging.INFO)
    
    def log_action(self,
                   user_id: int,
                   action: AuditAction,
                   details: Dict[str, Any] = None,
                   severity: AuditSeverity = AuditSeverity.LOW,
                   ip_address: str = None,
                   user_agent: str = None) -> str:
        """Log an audit action"""
        try:
            # Generate unique audit ID
            audit_id = str(uuid.uuid4())
            
            # Create audit log entry
            audit_entry = AuditLog(
                id=audit_id,
                user_id=user_id,
                action=action.value,
                details=json.dumps(details or {}),
                severity=severity.value,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.now()
            )
            
            # Save to database
            self.db.add(audit_entry)
            self.db.commit()
            
            # Log to file
            log_message = f"User {user_id} performed {action.value} - {json.dumps(details or {})}"
            self.logger.info(log_message)
            
            return audit_id
            
        except Exception as e:
            logger.error(f"Error logging audit action: {str(e)}")
            return None
    
    def log_login(self, user_id: int, ip_address: str = None, user_agent: str = None) -> str:
        """Log user login"""
        return self.log_action(
            user_id=user_id,
            action=AuditAction.LOGIN,
            details={'event': 'user_login'},
            severity=AuditSeverity.LOW,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_logout(self, user_id: int, ip_address: str = None) -> str:
        """Log user logout"""
        return self.log_action(
            user_id=user_id,
            action=AuditAction.LOGOUT,
            details={'event': 'user_logout'},
            severity=AuditSeverity.LOW,
            ip_address=ip_address
        )
    
    def log_file_upload(self, 
                       user_id: int, 
                       filename: str, 
                       file_size: int,
                       file_type: str,
                       success: bool,
                       error_message: str = None,
                       ip_address: str = None) -> str:
        """Log file upload"""
        details = {
            'filename': filename,
            'file_size': file_size,
            'file_type': file_type,
            'success': success
        }
        
        if error_message:
            details['error'] = error_message
        
        return self.log_action(
            user_id=user_id,
            action=AuditAction.FILE_UPLOAD,
            details=details,
            severity=AuditSeverity.MEDIUM if success else AuditSeverity.HIGH,
            ip_address=ip_address
        )
    
    def log_file_process(self,
                        user_id: int,
                        filename: str,
                        records_processed: int,
                        records_successful: int,
                        records_failed: int,
                        processing_time: float,
                        ip_address: str = None) -> str:
        """Log file processing"""
        success_rate = (records_successful / records_processed * 100) if records_processed > 0 else 0
        
        details = {
            'filename': filename,
            'records_processed': records_processed,
            'records_successful': records_successful,
            'records_failed': records_failed,
            'success_rate': round(success_rate, 2),
            'processing_time_seconds': round(processing_time, 2)
        }
        
        severity = AuditSeverity.LOW if success_rate >= 90 else AuditSeverity.MEDIUM
        
        return self.log_action(
            user_id=user_id,
            action=AuditAction.FILE_PROCESS,
            details=details,
            severity=severity,
            ip_address=ip_address
        )
    
    def log_data_export(self,
                       user_id: int,
                       export_type: str,
                       data_type: str,
                       record_count: int,
                       file_format: str,
                       ip_address: str = None) -> str:
        """Log data export"""
        details = {
            'export_type': export_type,
            'data_type': data_type,
            'record_count': record_count,
            'file_format': file_format
        }
        
        return self.log_action(
            user_id=user_id,
            action=AuditAction.DATA_EXPORT,
            details=details,
            severity=AuditSeverity.MEDIUM,
            ip_address=ip_address
        )
    
    def log_user_management(self,
                           admin_user_id: int,
                           target_user_id: int,
                           action_type: str,
                           changes: Dict[str, Any] = None,
                           ip_address: str = None) -> str:
        """Log user management actions"""
        action_map = {
            'create': AuditAction.USER_CREATE,
            'update': AuditAction.USER_UPDATE,
            'delete': AuditAction.USER_DELETE
        }
        
        details = {
            'target_user_id': target_user_id,
            'action_type': action_type,
            'changes': changes or {}
        }
        
        return self.log_action(
            user_id=admin_user_id,
            action=action_map.get(action_type, AuditAction.USER_UPDATE),
            details=details,
            severity=AuditSeverity.HIGH,
            ip_address=ip_address
        )
    
    def log_pharmacy_mapping(self,
                            user_id: int,
                            pharmacy_name: str,
                            mapped_pharmacy_id: str,
                            action: str,
                            confidence_score: float = None,
                            ip_address: str = None) -> str:
        """Log pharmacy mapping actions"""
        details = {
            'pharmacy_name': pharmacy_name,
            'mapped_pharmacy_id': mapped_pharmacy_id,
            'action': action
        }
        
        if confidence_score is not None:
            details['confidence_score'] = confidence_score
        
        action_type = AuditAction.PHARMACY_MAP if action == 'map' else AuditAction.PHARMACY_UNMAP
        
        return self.log_action(
            user_id=user_id,
            action=action_type,
            details=details,
            severity=AuditSeverity.MEDIUM,
            ip_address=ip_address
        )
    
    def log_settings_update(self,
                           user_id: int,
                           settings_changed: List[str],
                           old_values: Dict[str, Any] = None,
                           new_values: Dict[str, Any] = None,
                           ip_address: str = None) -> str:
        """Log settings updates"""
        details = {
            'settings_changed': settings_changed,
            'old_values': old_values or {},
            'new_values': new_values or {}
        }
        
        return self.log_action(
            user_id=user_id,
            action=AuditAction.SETTINGS_UPDATE,
            details=details,
            severity=AuditSeverity.MEDIUM,
            ip_address=ip_address
        )
    
    def log_report_generation(self,
                             user_id: int,
                             report_type: str,
                             report_format: str,
                             record_count: int,
                             ip_address: str = None) -> str:
        """Log report generation"""
        details = {
            'report_type': report_type,
            'report_format': report_format,
            'record_count': record_count
        }
        
        return self.log_action(
            user_id=user_id,
            action=AuditAction.REPORT_GENERATE,
            details=details,
            severity=AuditSeverity.LOW,
            ip_address=ip_address
        )
    
    def log_system_backup(self,
                         user_id: int,
                         backup_type: str,
                         backup_size: int = None,
                         success: bool = True,
                         ip_address: str = None) -> str:
        """Log system backup"""
        details = {
            'backup_type': backup_type,
            'success': success
        }
        
        if backup_size:
            details['backup_size_mb'] = backup_size
        
        return self.log_action(
            user_id=user_id,
            action=AuditAction.SYSTEM_BACKUP,
            details=details,
            severity=AuditSeverity.HIGH,
            ip_address=ip_address
        )
    
    def get_audit_logs(self,
                      user_id: int = None,
                      action: str = None,
                      severity: str = None,
                      start_date: datetime = None,
                      end_date: datetime = None,
                      limit: int = 100,
                      offset: int = 0) -> List[Dict[str, Any]]:
        """Get audit logs with filtering"""
        try:
            query = self.db.query(AuditLog)
            
            # Apply filters
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            
            if action:
                query = query.filter(AuditLog.action == action)
            
            if severity:
                query = query.filter(AuditLog.severity == severity)
            
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            
            # Order by timestamp descending
            query = query.order_by(desc(AuditLog.timestamp))
            
            # Apply pagination
            logs = query.offset(offset).limit(limit).all()
            
            # Convert to dictionary format
            result = []
            for log in logs:
                result.append({
                    'id': log.id,
                    'user_id': log.user_id,
                    'action': log.action,
                    'details': json.loads(log.details) if log.details else {},
                    'severity': log.severity,
                    'ip_address': log.ip_address,
                    'user_agent': log.user_agent,
                    'timestamp': log.timestamp.isoformat()
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting audit logs: {str(e)}")
            return []
    
    def get_audit_statistics(self,
                           start_date: datetime = None,
                           end_date: datetime = None) -> Dict[str, Any]:
        """Get audit statistics"""
        try:
            query = self.db.query(AuditLog)
            
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            
            # Get total count
            total_logs = query.count()
            
            # Get counts by action
            action_counts = {}
            for log in query.all():
                action = log.action
                action_counts[action] = action_counts.get(action, 0) + 1
            
            # Get counts by severity
            severity_counts = {}
            for log in query.all():
                severity = log.severity
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Get unique users
            unique_users = query.with_entities(AuditLog.user_id).distinct().count()
            
            return {
                'total_logs': total_logs,
                'unique_users': unique_users,
                'action_counts': action_counts,
                'severity_counts': severity_counts,
                'period': {
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting audit statistics: {str(e)}")
            return {}
    
    def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """Clean up old audit logs"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Count logs to be deleted
            old_logs_count = self.db.query(AuditLog).filter(
                AuditLog.timestamp < cutoff_date
            ).count()
            
            # Delete old logs
            self.db.query(AuditLog).filter(
                AuditLog.timestamp < cutoff_date
            ).delete()
            
            self.db.commit()
            
            logger.info(f"Cleaned up {old_logs_count} old audit logs")
            return old_logs_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {str(e)}")
            return 0
    
    def export_audit_logs(self,
                         start_date: datetime = None,
                         end_date: datetime = None,
                         format: str = 'csv') -> str:
        """Export audit logs to file"""
        try:
            logs = self.get_audit_logs(
                start_date=start_date,
                end_date=end_date,
                limit=10000  # Large limit for export
            )
            
            if not logs:
                return None
            
            # Convert to DataFrame
            import pandas as pd
            df = pd.DataFrame(logs)
            
            # Create temporary file
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{format}')
            temp_filename = temp_file.name
            temp_file.close()
            
            # Export based on format
            if format == 'csv':
                df.to_csv(temp_filename, index=False)
            elif format == 'excel':
                df.to_excel(temp_filename, index=False)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            return temp_filename
            
        except Exception as e:
            logger.error(f"Error exporting audit logs: {str(e)}")
            return None
