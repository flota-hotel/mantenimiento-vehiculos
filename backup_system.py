#!/usr/bin/env python3
"""
Sistema de Backup Automático para Base de Datos Vehicular
Crear backups automáticos cada hora y mantener historial
"""

import sqlite3
import shutil
import os
import schedule
import time
from datetime import datetime, timedelta
import logging
import json
import gzip

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración de backup
BACKUP_CONFIG = {
    "source_db": "vehicular_system.db",
    "backup_dir": "backups",
    "max_hourly_backups": 24,     # 24 horas de backups
    "max_daily_backups": 7,       # 7 días de backups diarios
    "max_weekly_backups": 4,      # 4 semanas de backups semanales
    "max_monthly_backups": 6      # 6 meses de backups mensuales
}

class DatabaseBackupManager:
    def __init__(self):
        self.ensure_backup_directories()
    
    def ensure_backup_directories(self):
        """Crear directorios de backup si no existen"""
        dirs = [
            BACKUP_CONFIG["backup_dir"],
            f"{BACKUP_CONFIG['backup_dir']}/hourly",
            f"{BACKUP_CONFIG['backup_dir']}/daily", 
            f"{BACKUP_CONFIG['backup_dir']}/weekly",
            f"{BACKUP_CONFIG['backup_dir']}/monthly",
            f"{BACKUP_CONFIG['backup_dir']}/manual"
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
        logger.info("✅ Directorios de backup verificados")
    
    def create_backup(self, backup_type="manual", description=""):
        """Crear backup de la base de datos"""
        try:
            if not os.path.exists(BACKUP_CONFIG["source_db"]):
                logger.error("❌ Base de datos fuente no encontrada")
                return False
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"vehicular_backup_{backup_type}_{timestamp}.db"
            backup_path = f"{BACKUP_CONFIG['backup_dir']}/{backup_type}/{backup_filename}"
            
            # Crear backup usando sqlite3 backup API (más seguro que copy)
            source_conn = sqlite3.connect(BACKUP_CONFIG["source_db"])
            backup_conn = sqlite3.connect(backup_path)
            
            source_conn.backup(backup_conn)
            source_conn.close()
            backup_conn.close()
            
            # Crear archivo de metadatos
            metadata = {
                "backup_type": backup_type,
                "timestamp": timestamp,
                "datetime": datetime.now().isoformat(),
                "description": description,
                "file_size": os.path.getsize(backup_path),
                "source_file": BACKUP_CONFIG["source_db"]
            }
            
            metadata_path = backup_path.replace('.db', '.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Comprimir backup si es mayor a 1MB
            if os.path.getsize(backup_path) > 1024 * 1024:
                compressed_path = backup_path + '.gz'
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(backup_path)
                backup_path = compressed_path
            
            logger.info(f"✅ Backup creado: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"❌ Error creando backup: {e}")
            return False
    
    def cleanup_old_backups(self):
        """Limpiar backups antiguos según la política de retención"""
        try:
            # Limpiar backups por hora
            self._cleanup_directory("hourly", BACKUP_CONFIG["max_hourly_backups"])
            
            # Limpiar backups diarios
            self._cleanup_directory("daily", BACKUP_CONFIG["max_daily_backups"])
            
            # Limpiar backups semanales
            self._cleanup_directory("weekly", BACKUP_CONFIG["max_weekly_backups"])
            
            # Limpiar backups mensuales
            self._cleanup_directory("monthly", BACKUP_CONFIG["max_monthly_backups"])
            
            logger.info("✅ Limpieza de backups completada")
            
        except Exception as e:
            logger.error(f"❌ Error en limpieza de backups: {e}")
    
    def _cleanup_directory(self, backup_type, max_files):
        """Limpiar archivos antiguos en un directorio específico"""
        backup_dir = f"{BACKUP_CONFIG['backup_dir']}/{backup_type}"
        
        if not os.path.exists(backup_dir):
            return
        
        # Obtener todos los archivos .db y .db.gz
        files = [f for f in os.listdir(backup_dir) 
                if f.endswith('.db') or f.endswith('.db.gz')]
        
        # Ordenar por fecha de modificación
        files.sort(key=lambda x: os.path.getmtime(f"{backup_dir}/{x}"))
        
        # Eliminar archivos más antiguos si superan el límite
        if len(files) > max_files:
            files_to_delete = files[:-max_files]
            for file in files_to_delete:
                try:
                    os.remove(f"{backup_dir}/{file}")
                    # Eliminar metadata también
                    metadata_file = file.replace('.db.gz', '.json').replace('.db', '.json')
                    metadata_path = f"{backup_dir}/{metadata_file}"
                    if os.path.exists(metadata_path):
                        os.remove(metadata_path)
                    logger.info(f"🗑️  Backup antiguo eliminado: {file}")
                except Exception as e:
                    logger.error(f"❌ Error eliminando {file}: {e}")
    
    def restore_backup(self, backup_path):
        """Restaurar base de datos desde backup"""
        try:
            if not os.path.exists(backup_path):
                logger.error("❌ Archivo de backup no encontrado")
                return False
            
            # Crear backup de seguridad antes de restaurar
            current_backup = self.create_backup("pre_restore", "Backup antes de restauración")
            
            # Descomprimir si es necesario
            temp_file = None
            if backup_path.endswith('.gz'):
                temp_file = backup_path.replace('.gz', '_temp')
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                source_file = temp_file
            else:
                source_file = backup_path
            
            # Restaurar base de datos
            shutil.copy2(source_file, BACKUP_CONFIG["source_db"])
            
            # Limpiar archivo temporal
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            
            logger.info(f"✅ Base de datos restaurada desde: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error restaurando backup: {e}")
            return False
    
    def list_backups(self):
        """Listar todos los backups disponibles"""
        backups = []
        backup_types = ["hourly", "daily", "weekly", "monthly", "manual"]
        
        for backup_type in backup_types:
            backup_dir = f"{BACKUP_CONFIG['backup_dir']}/{backup_type}"
            if not os.path.exists(backup_dir):
                continue
                
            files = [f for f in os.listdir(backup_dir) 
                    if f.endswith('.db') or f.endswith('.db.gz')]
            
            for file in files:
                file_path = f"{backup_dir}/{file}"
                metadata_file = file.replace('.db.gz', '.json').replace('.db', '.json')
                metadata_path = f"{backup_dir}/{metadata_file}"
                
                backup_info = {
                    "file": file,
                    "path": file_path,
                    "type": backup_type,
                    "size": os.path.getsize(file_path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                }
                
                # Cargar metadata si existe
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                            backup_info.update(metadata)
                    except:
                        pass
                
                backups.append(backup_info)
        
        # Ordenar por fecha
        backups.sort(key=lambda x: x['modified'], reverse=True)
        return backups

# Funciones de scheduleo
def hourly_backup():
    """Backup cada hora"""
    backup_manager = DatabaseBackupManager()
    backup_manager.create_backup("hourly", f"Backup automático cada hora")
    backup_manager.cleanup_old_backups()

def daily_backup():
    """Backup diario"""
    backup_manager = DatabaseBackupManager()
    backup_manager.create_backup("daily", f"Backup diario automático")

def weekly_backup():
    """Backup semanal"""
    backup_manager = DatabaseBackupManager()
    backup_manager.create_backup("weekly", f"Backup semanal automático")

def monthly_backup():
    """Backup mensual"""
    backup_manager = DatabaseBackupManager()
    backup_manager.create_backup("monthly", f"Backup mensual automático")

def start_backup_scheduler():
    """Iniciar el programador de backups automáticos"""
    logger.info("🚀 Iniciando sistema de backup automático...")
    
    # Programar backups
    schedule.every().hour.do(hourly_backup)
    schedule.every().day.at("02:00").do(daily_backup)
    schedule.every().monday.at("03:00").do(weekly_backup)  
    schedule.every().month.do(monthly_backup)
    
    # Crear backup inicial
    backup_manager = DatabaseBackupManager()
    backup_manager.create_backup("manual", "Backup inicial del sistema")
    
    logger.info("✅ Sistema de backup configurado:")
    logger.info("  📅 Cada hora: backup automático")
    logger.info("  📅 Diario: 02:00 AM")
    logger.info("  📅 Semanal: Lunes 03:00 AM") 
    logger.info("  📅 Mensual: Primer día del mes")
    
    # Loop principal
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verificar cada minuto

if __name__ == "__main__":
    start_backup_scheduler()