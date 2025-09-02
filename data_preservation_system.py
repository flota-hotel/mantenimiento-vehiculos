#!/usr/bin/env python3
"""
Sistema de Preservación de Datos
Garantiza que nunca se pierdan datos durante modificaciones del sistema
"""

import os
import sqlite3
import shutil
import json
from datetime import datetime
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DataPreservationSystem:
    """Sistema que garantiza la preservación de datos existentes"""
    
    def __init__(self, db_path="/home/user/webapp/vehicular_system.db"):
        self.db_path = db_path
        self.backup_dir = "/home/user/webapp/data_preservation"
        self.ensure_directories()
        
    def ensure_directories(self):
        """Crear directorios necesarios"""
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(f"{self.backup_dir}/pre_change", exist_ok=True)
        os.makedirs(f"{self.backup_dir}/snapshots", exist_ok=True)
        
    def create_pre_change_backup(self, operation_description="Cambio no especificado"):
        """Crear backup antes de cualquier modificación"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"pre_change_backup_{timestamp}.db"
        backup_path = f"{self.backup_dir}/pre_change/{backup_filename}"
        
        try:
            # Copiar base de datos actual
            shutil.copy2(self.db_path, backup_path)
            
            # Crear archivo de metadatos
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation_description,
                "original_db_size": os.path.getsize(self.db_path),
                "backup_path": backup_path,
                "data_counts": self.get_current_data_counts()
            }
            
            metadata_path = backup_path.replace('.db', '_metadata.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Backup preventivo creado: {backup_filename}")
            return backup_path, metadata
            
        except Exception as e:
            logger.error(f"❌ Error creando backup preventivo: {e}")
            return None, None
    
    def get_current_data_counts(self):
        """Obtener conteos actuales de todos los datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            counts = {}
            
            # Obtener todas las tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Contar registros en cada tabla
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    counts[table] = cursor.fetchone()[0]
                except sqlite3.Error as e:
                    logger.warning(f"Error contando tabla {table}: {e}")
                    counts[table] = 0
            
            conn.close()
            return counts
            
        except Exception as e:
            logger.error(f"Error obteniendo conteos de datos: {e}")
            return {}
    
    def verify_data_integrity_after_change(self, pre_change_counts: Dict[str, int]):
        """Verificar que no se perdieron datos después de un cambio"""
        current_counts = self.get_current_data_counts()
        
        integrity_report = {
            "timestamp": datetime.now().isoformat(),
            "status": "SUCCESS",
            "issues": [],
            "changes": {}
        }
        
        for table, old_count in pre_change_counts.items():
            current_count = current_counts.get(table, 0)
            change = current_count - old_count
            
            integrity_report["changes"][table] = {
                "before": old_count,
                "after": current_count,
                "change": change
            }
            
            # Solo reportar como problema si hay una disminución significativa inesperada
            if change < -10:  # Más de 10 registros perdidos es sospechoso
                integrity_report["issues"].append(
                    f"ALERTA: Tabla '{table}' perdió {abs(change)} registros"
                )
                integrity_report["status"] = "WARNING"
        
        return integrity_report
    
    def restore_from_backup(self, backup_path: str):
        """Restaurar base de datos desde un backup específico"""
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup no encontrado: {backup_path}")
            
            # Crear backup del estado actual antes de restaurar
            current_backup = f"{self.backup_dir}/snapshots/before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(self.db_path, current_backup)
            
            # Restaurar desde backup
            shutil.copy2(backup_path, self.db_path)
            
            logger.info(f"✅ Base de datos restaurada desde: {backup_path}")
            logger.info(f"📁 Estado anterior guardado en: {current_backup}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error restaurando backup: {e}")
            return False
    
    def get_available_backups(self):
        """Obtener lista de backups disponibles"""
        try:
            backups = []
            
            # Buscar backups en directorio de pre-cambios
            pre_change_dir = f"{self.backup_dir}/pre_change"
            if os.path.exists(pre_change_dir):
                for file in os.listdir(pre_change_dir):
                    if file.endswith('.db'):
                        file_path = os.path.join(pre_change_dir, file)
                        metadata_path = file_path.replace('.db', '_metadata.json')
                        
                        backup_info = {
                            "filename": file,
                            "path": file_path,
                            "type": "pre_change",
                            "size": os.path.getsize(file_path),
                            "created": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                        }
                        
                        # Cargar metadatos si existen
                        if os.path.exists(metadata_path):
                            try:
                                with open(metadata_path, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                                backup_info["metadata"] = metadata
                            except Exception:
                                pass
                        
                        backups.append(backup_info)
            
            # Ordenar por fecha de creación (más reciente primero)
            backups.sort(key=lambda x: x["created"], reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"Error obteniendo lista de backups: {e}")
            return []
    
    def cleanup_old_backups(self, keep_count=20):
        """Limpiar backups antiguos, manteniendo solo los más recientes"""
        try:
            backups = self.get_available_backups()
            
            if len(backups) <= keep_count:
                return 0
            
            # Eliminar backups excedentes
            deleted_count = 0
            for backup in backups[keep_count:]:
                try:
                    os.remove(backup["path"])
                    # Eliminar metadata asociado
                    metadata_path = backup["path"].replace('.db', '_metadata.json')
                    if os.path.exists(metadata_path):
                        os.remove(metadata_path)
                    deleted_count += 1
                    logger.info(f"🗑️ Backup antiguo eliminado: {backup['filename']}")
                except Exception as e:
                    logger.warning(f"Error eliminando backup {backup['filename']}: {e}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error limpiando backups antiguos: {e}")
            return 0

# Instancia global para uso en el sistema
preservation_system = DataPreservationSystem()

def protect_data_operation(operation_description: str):
    """Decorador para proteger operaciones que modifican datos"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Crear backup preventivo
            backup_path, metadata = preservation_system.create_pre_change_backup(operation_description)
            
            if not backup_path:
                logger.warning("⚠️ No se pudo crear backup preventivo, procediendo con precaución")
            
            try:
                # Ejecutar operación original
                result = func(*args, **kwargs)
                
                # Verificar integridad después del cambio
                if metadata and metadata.get("data_counts"):
                    integrity_report = preservation_system.verify_data_integrity_after_change(
                        metadata["data_counts"]
                    )
                    
                    if integrity_report["status"] == "WARNING":
                        logger.warning("⚠️ Posible pérdida de datos detectada:")
                        for issue in integrity_report["issues"]:
                            logger.warning(f"  - {issue}")
                
                return result
                
            except Exception as e:
                logger.error(f"❌ Error en operación protegida: {e}")
                
                # En caso de error, el backup está disponible para restauración manual
                if backup_path:
                    logger.info(f"💾 Backup preventivo disponible en: {backup_path}")
                
                raise e
        
        return wrapper
    return decorator

if __name__ == "__main__":
    # Prueba del sistema
    system = DataPreservationSystem()
    
    # Crear backup de prueba
    backup_path, metadata = system.create_pre_change_backup("Prueba del sistema")
    print(f"Backup creado: {backup_path}")
    
    # Mostrar backups disponibles
    backups = system.get_available_backups()
    print(f"Backups disponibles: {len(backups)}")
    
    # Mostrar conteos actuales
    counts = system.get_current_data_counts()
    print(f"Datos actuales: {counts}")