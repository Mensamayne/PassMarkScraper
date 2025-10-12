"""Database backup utilities."""
import shutil
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def create_backup(db_path: str = "benchmarks.db") -> str:
    """
    Create backup of database.
    
    Returns:
        Path to backup file
    """
    try:
        # Create backups directory
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"benchmarks_{timestamp}.db"
        
        # Copy database
        db_file = Path(db_path)
        if db_file.exists():
            shutil.copy2(db_file, backup_file)
            logger.info(f"Backup created: {backup_file}")
            
            # Cleanup old backups
            cleanup_old_backups(backup_dir, keep_count=7)
            
            return str(backup_file)
        else:
            logger.warning(f"Database file not found: {db_path}")
            return None
            
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        raise


def cleanup_old_backups(backup_dir: Path, keep_count: int = 7):
    """
    Keep only the most recent N backups.
    
    Args:
        backup_dir: Directory containing backups
        keep_count: Number of backups to keep
    """
    try:
        # Get all backup files
        backups = sorted(
            backup_dir.glob("benchmarks_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # Remove old backups
        for old_backup in backups[keep_count:]:
            old_backup.unlink()
            logger.info(f"Removed old backup: {old_backup.name}")
            
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")


def list_backups() -> list[dict]:
    """
    List all available backups.
    
    Returns:
        List of backup info dicts
    """
    backup_dir = Path("backups")
    if not backup_dir.exists():
        return []
    
    backups = []
    for backup_file in sorted(backup_dir.glob("benchmarks_*.db"), key=lambda p: p.stat().st_mtime, reverse=True):
        stat = backup_file.stat()
        backups.append({
            "filename": backup_file.name,
            "path": str(backup_file),
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    
    return backups


def restore_backup(backup_filename: str, db_path: str = "benchmarks.db") -> bool:
    """
    Restore database from backup.
    
    Args:
        backup_filename: Name of backup file
        db_path: Target database path
        
    Returns:
        True if successful
    """
    try:
        backup_file = Path("backups") / backup_filename
        
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup not found: {backup_filename}")
        
        # Create backup of current DB before restore
        current_db = Path(db_path)
        if current_db.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pre_restore_backup = Path("backups") / f"pre_restore_{timestamp}.db"
            shutil.copy2(current_db, pre_restore_backup)
            logger.info(f"Created pre-restore backup: {pre_restore_backup}")
        
        # Restore from backup
        shutil.copy2(backup_file, db_path)
        logger.info(f"Database restored from: {backup_filename}")
        
        return True
        
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        raise

