"""
Backup and Recovery System for Pharmacy Revenue Management System
Version: 2.0
"""

import os
import shutil
import gzip
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import subprocess
import tempfile
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import redis
import schedule
import time
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupManager:
    """Comprehensive backup and recovery system"""
    
    def __init__(self, 
                 db_config: Dict[str, str],
                 redis_config: Dict[str, str],
                 backup_dir: str = "backups"):
        self.db_config = db_config
        self.redis_config = redis_config
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.backup_dir / "database").mkdir(exist_ok=True)
        (self.backup_dir / "redis").mkdir(exist_ok=True)
        (self.backup_dir / "files").mkdir(exist_ok=True)
        (self.backup_dir / "config").mkdir(exist_ok=True)
        
        self.scheduler_running = False
    
    def create_full_backup(self, 
                          backup_name: str = None,
                          compress: bool = True) -> Dict[str, Any]:
        """Create a full system backup"""
        try:
            if not backup_name:
                backup_name = f"full_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Starting full backup: {backup_name}")
            
            backup_info = {
                'backup_name': backup_name,
                'start_time': datetime.now().isoformat(),
                'components': {},
                'success': False,
                'error': None
            }
            
            # Backup database
            db_backup = self._backup_database(backup_name, compress)
            backup_info['components']['database'] = db_backup
            
            # Backup Redis
            redis_backup = self._backup_redis(backup_name, compress)
            backup_info['components']['redis'] = redis_backup
            
            # Backup application files
            files_backup = self._backup_application_files(backup_name, compress)
            backup_info['components']['files'] = files_backup
            
            # Backup configuration
            config_backup = self._backup_configuration(backup_name, compress)
            backup_info['components']['config'] = config_backup
            
            # Create backup manifest
            manifest_path = self._create_backup_manifest(backup_name, backup_info)
            backup_info['manifest'] = str(manifest_path)
            
            # Check if all components succeeded
            all_success = all(
                component.get('success', False) 
                for component in backup_info['components'].values()
            )
            
            backup_info['success'] = all_success
            backup_info['end_time'] = datetime.now().isoformat()
            
            if all_success:
                logger.info(f"Full backup completed successfully: {backup_name}")
            else:
                logger.error(f"Full backup completed with errors: {backup_name}")
            
            return backup_info
            
        except Exception as e:
            logger.error(f"Error creating full backup: {str(e)}")
            return {
                'backup_name': backup_name,
                'success': False,
                'error': str(e),
                'end_time': datetime.now().isoformat()
            }
    
    def _backup_database(self, backup_name: str, compress: bool) -> Dict[str, Any]:
        """Backup PostgreSQL database"""
        try:
            logger.info("Backing up database...")
            
            # Create database backup using pg_dump
            db_backup_file = self.backup_dir / "database" / f"{backup_name}_database.sql"
            
            # Build pg_dump command
            pg_dump_cmd = [
                'pg_dump',
                '-h', self.db_config['host'],
                '-p', str(self.db_config['port']),
                '-U', self.db_config['user'],
                '-d', self.db_config['database'],
                '--no-password',
                '--verbose',
                '--clean',
                '--create',
                '--if-exists'
            ]
            
            # Execute pg_dump
            with open(db_backup_file, 'w') as f:
                result = subprocess.run(
                    pg_dump_cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True,
                    env={**os.environ, 'PGPASSWORD': self.db_config['password']}
                )
            
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            # Compress if requested
            if compress:
                compressed_file = f"{db_backup_file}.gz"
                with open(db_backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(db_backup_file)
                db_backup_file = Path(compressed_file)
            
            # Get file size
            file_size = db_backup_file.stat().st_size
            
            logger.info(f"Database backup completed: {db_backup_file}")
            
            return {
                'success': True,
                'file_path': str(db_backup_file),
                'file_size': file_size,
                'compressed': compress
            }
            
        except Exception as e:
            logger.error(f"Error backing up database: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _backup_redis(self, backup_name: str, compress: bool) -> Dict[str, Any]:
        """Backup Redis data"""
        try:
            logger.info("Backing up Redis...")
            
            # Connect to Redis
            r = redis.Redis(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                password=self.redis_config.get('password'),
                decode_responses=True
            )
            
            # Get all keys
            keys = r.keys('*')
            
            # Create Redis backup file
            redis_backup_file = self.backup_dir / "redis" / f"{backup_name}_redis.json"
            
            redis_data = {}
            for key in keys:
                key_type = r.type(key)
                
                if key_type == 'string':
                    redis_data[key] = {'type': 'string', 'value': r.get(key)}
                elif key_type == 'hash':
                    redis_data[key] = {'type': 'hash', 'value': r.hgetall(key)}
                elif key_type == 'list':
                    redis_data[key] = {'type': 'list', 'value': r.lrange(key, 0, -1)}
                elif key_type == 'set':
                    redis_data[key] = {'type': 'set', 'value': list(r.smembers(key))}
                elif key_type == 'zset':
                    redis_data[key] = {'type': 'zset', 'value': r.zrange(key, 0, -1, withscores=True)}
            
            # Save to file
            with open(redis_backup_file, 'w') as f:
                json.dump(redis_data, f, indent=2, default=str)
            
            # Compress if requested
            if compress:
                compressed_file = f"{redis_backup_file}.gz"
                with open(redis_backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(redis_backup_file)
                redis_backup_file = Path(compressed_file)
            
            # Get file size
            file_size = redis_backup_file.stat().st_size
            
            logger.info(f"Redis backup completed: {redis_backup_file}")
            
            return {
                'success': True,
                'file_path': str(redis_backup_file),
                'file_size': file_size,
                'keys_backed_up': len(keys),
                'compressed': compress
            }
            
        except Exception as e:
            logger.error(f"Error backing up Redis: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _backup_application_files(self, backup_name: str, compress: bool) -> Dict[str, Any]:
        """Backup application files"""
        try:
            logger.info("Backing up application files...")
            
            # Define files to backup
            files_to_backup = [
                'app/',
                'requirements.txt',
                'Dockerfile',
                'docker-compose.yml',
                'nginx.conf',
                'deploy.sh'
            ]
            
            files_backup_dir = self.backup_dir / "files" / backup_name
            files_backup_dir.mkdir(exist_ok=True)
            
            # Copy files
            for file_path in files_to_backup:
                if os.path.exists(file_path):
                    if os.path.isdir(file_path):
                        shutil.copytree(file_path, files_backup_dir / file_path)
                    else:
                        shutil.copy2(file_path, files_backup_dir / file_path)
            
            # Create archive if compress is requested
            if compress:
                archive_path = self.backup_dir / "files" / f"{backup_name}_files.tar.gz"
                shutil.make_archive(
                    str(archive_path.with_suffix('')),
                    'gztar',
                    str(files_backup_dir)
                )
                shutil.rmtree(files_backup_dir)
                files_backup_file = archive_path
            else:
                files_backup_file = files_backup_dir
            
            # Get total size
            if compress:
                file_size = files_backup_file.stat().st_size
            else:
                file_size = sum(
                    f.stat().st_size for f in files_backup_dir.rglob('*') if f.is_file()
                )
            
            logger.info(f"Application files backup completed: {files_backup_file}")
            
            return {
                'success': True,
                'file_path': str(files_backup_file),
                'file_size': file_size,
                'compressed': compress
            }
            
        except Exception as e:
            logger.error(f"Error backing up application files: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _backup_configuration(self, backup_name: str, compress: bool) -> Dict[str, Any]:
        """Backup configuration files"""
        try:
            logger.info("Backing up configuration...")
            
            config_backup_file = self.backup_dir / "config" / f"{backup_name}_config.json"
            
            config_data = {
                'database': {
                    'host': self.db_config['host'],
                    'port': self.db_config['port'],
                    'database': self.db_config['database'],
                    'user': self.db_config['user']
                    # Don't include password in backup
                },
                'redis': {
                    'host': self.redis_config['host'],
                    'port': self.redis_config['port']
                    # Don't include password in backup
                },
                'backup_info': {
                    'created_at': datetime.now().isoformat(),
                    'backup_name': backup_name,
                    'version': '2.0'
                }
            }
            
            # Save configuration
            with open(config_backup_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            # Compress if requested
            if compress:
                compressed_file = f"{config_backup_file}.gz"
                with open(config_backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(config_backup_file)
                config_backup_file = Path(compressed_file)
            
            # Get file size
            file_size = config_backup_file.stat().st_size
            
            logger.info(f"Configuration backup completed: {config_backup_file}")
            
            return {
                'success': True,
                'file_path': str(config_backup_file),
                'file_size': file_size,
                'compressed': compress
            }
            
        except Exception as e:
            logger.error(f"Error backing up configuration: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_backup_manifest(self, backup_name: str, backup_info: Dict[str, Any]) -> Path:
        """Create backup manifest file"""
        manifest_file = self.backup_dir / f"{backup_name}_manifest.json"
        
        with open(manifest_file, 'w') as f:
            json.dump(backup_info, f, indent=2, default=str)
        
        return manifest_file
    
    def restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """Restore from backup"""
        try:
            logger.info(f"Starting restore from backup: {backup_name}")
            
            # Load backup manifest
            manifest_file = self.backup_dir / f"{backup_name}_manifest.json"
            if not manifest_file.exists():
                raise Exception(f"Backup manifest not found: {manifest_file}")
            
            with open(manifest_file, 'r') as f:
                backup_info = json.load(f)
            
            restore_info = {
                'backup_name': backup_name,
                'start_time': datetime.now().isoformat(),
                'components': {},
                'success': False,
                'error': None
            }
            
            # Restore database
            if 'database' in backup_info['components']:
                db_restore = self._restore_database(backup_name, backup_info['components']['database'])
                restore_info['components']['database'] = db_restore
            
            # Restore Redis
            if 'redis' in backup_info['components']:
                redis_restore = self._restore_redis(backup_name, backup_info['components']['redis'])
                restore_info['components']['redis'] = redis_restore
            
            # Check if all components succeeded
            all_success = all(
                component.get('success', False) 
                for component in restore_info['components'].values()
            )
            
            restore_info['success'] = all_success
            restore_info['end_time'] = datetime.now().isoformat()
            
            if all_success:
                logger.info(f"Restore completed successfully: {backup_name}")
            else:
                logger.error(f"Restore completed with errors: {backup_name}")
            
            return restore_info
            
        except Exception as e:
            logger.error(f"Error restoring backup: {str(e)}")
            return {
                'backup_name': backup_name,
                'success': False,
                'error': str(e),
                'end_time': datetime.now().isoformat()
            }
    
    def _restore_database(self, backup_name: str, db_backup_info: Dict[str, Any]) -> Dict[str, Any]:
        """Restore database from backup"""
        try:
            logger.info("Restoring database...")
            
            db_backup_file = Path(db_backup_info['file_path'])
            
            # Decompress if needed
            if db_backup_info.get('compressed', False):
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sql')
                with gzip.open(db_backup_file, 'rb') as f_in:
                    with open(temp_file.name, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                db_backup_file = Path(temp_file.name)
            
            # Restore database using psql
            with open(db_backup_file, 'r') as f:
                result = subprocess.run(
                    ['psql', '-h', self.db_config['host'], '-p', str(self.db_config['port']), 
                     '-U', self.db_config['user'], '-d', 'postgres'],
                    stdin=f,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env={**os.environ, 'PGPASSWORD': self.db_config['password']}
                )
            
            if result.returncode != 0:
                raise Exception(f"psql restore failed: {result.stderr}")
            
            logger.info("Database restore completed")
            
            return {
                'success': True,
                'message': 'Database restored successfully'
            }
            
        except Exception as e:
            logger.error(f"Error restoring database: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _restore_redis(self, backup_name: str, redis_backup_info: Dict[str, Any]) -> Dict[str, Any]:
        """Restore Redis from backup"""
        try:
            logger.info("Restoring Redis...")
            
            redis_backup_file = Path(redis_backup_info['file_path'])
            
            # Decompress if needed
            if redis_backup_info.get('compressed', False):
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
                with gzip.open(redis_backup_file, 'rb') as f_in:
                    with open(temp_file.name, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                redis_backup_file = Path(temp_file.name)
            
            # Load Redis data
            with open(redis_backup_file, 'r') as f:
                redis_data = json.load(f)
            
            # Connect to Redis
            r = redis.Redis(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                password=self.redis_config.get('password'),
                decode_responses=True
            )
            
            # Clear existing data
            r.flushdb()
            
            # Restore data
            for key, data in redis_data.items():
                key_type = data['type']
                value = data['value']
                
                if key_type == 'string':
                    r.set(key, value)
                elif key_type == 'hash':
                    r.hset(key, mapping=value)
                elif key_type == 'list':
                    for item in value:
                        r.rpush(key, item)
                elif key_type == 'set':
                    for item in value:
                        r.sadd(key, item)
                elif key_type == 'zset':
                    for item, score in value:
                        r.zadd(key, {item: score})
            
            logger.info("Redis restore completed")
            
            return {
                'success': True,
                'message': f'Redis restored with {len(redis_data)} keys'
            }
            
        except Exception as e:
            logger.error(f"Error restoring Redis: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        try:
            backups = []
            
            # Find all manifest files
            for manifest_file in self.backup_dir.glob("*_manifest.json"):
                with open(manifest_file, 'r') as f:
                    backup_info = json.load(f)
                
                # Get backup size
                total_size = 0
                for component in backup_info.get('components', {}).values():
                    if 'file_size' in component:
                        total_size += component['file_size']
                
                backups.append({
                    'backup_name': backup_info['backup_name'],
                    'created_at': backup_info.get('start_time'),
                    'success': backup_info.get('success', False),
                    'total_size': total_size,
                    'components': list(backup_info.get('components', {}).keys())
                })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {str(e)}")
            return []
    
    def delete_backup(self, backup_name: str) -> bool:
        """Delete a backup"""
        try:
            logger.info(f"Deleting backup: {backup_name}")
            
            # Find and delete all files related to this backup
            deleted_files = 0
            
            for pattern in [f"{backup_name}*", f"*{backup_name}*"]:
                for file_path in self.backup_dir.rglob(pattern):
                    if file_path.is_file():
                        file_path.unlink()
                        deleted_files += 1
            
            logger.info(f"Deleted {deleted_files} files for backup: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting backup: {str(e)}")
            return False
    
    def cleanup_old_backups(self, days_to_keep: int = 30) -> int:
        """Clean up old backups"""
        try:
            logger.info(f"Cleaning up backups older than {days_to_keep} days")
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            for manifest_file in self.backup_dir.glob("*_manifest.json"):
                with open(manifest_file, 'r') as f:
                    backup_info = json.load(f)
                
                backup_date = datetime.fromisoformat(backup_info.get('start_time', ''))
                
                if backup_date < cutoff_date:
                    backup_name = backup_info['backup_name']
                    if self.delete_backup(backup_name):
                        deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old backups")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {str(e)}")
            return 0
    
    def setup_automated_backups(self, 
                               daily_time: str = "02:00",
                               weekly_day: str = "sunday",
                               monthly_day: int = 1) -> None:
        """Setup automated backup schedule"""
        try:
            logger.info("Setting up automated backups...")
            
            # Schedule daily backups
            schedule.every().day.at(daily_time).do(
                self.create_full_backup,
                backup_name=f"daily_{datetime.now().strftime('%Y%m%d')}",
                compress=True
            )
            
            # Schedule weekly backups
            getattr(schedule.every(), weekly_day.lower()).at("03:00").do(
                self.create_full_backup,
                backup_name=f"weekly_{datetime.now().strftime('%Y%m%d')}",
                compress=True
            )
            
            # Schedule monthly backups
            schedule.every().month.do(
                self.create_full_backup,
                backup_name=f"monthly_{datetime.now().strftime('%Y%m%d')}",
                compress=True
            )
            
            # Start scheduler in background thread
            if not self.scheduler_running:
                self.scheduler_running = True
                scheduler_thread = threading.Thread(target=self._run_scheduler)
                scheduler_thread.daemon = True
                scheduler_thread.start()
            
            logger.info("Automated backups scheduled successfully")
            
        except Exception as e:
            logger.error(f"Error setting up automated backups: {str(e)}")
    
    def _run_scheduler(self):
        """Run the backup scheduler"""
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop_automated_backups(self):
        """Stop automated backups"""
        self.scheduler_running = False
        schedule.clear()
        logger.info("Automated backups stopped")
