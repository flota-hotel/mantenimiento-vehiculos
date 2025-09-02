#!/usr/bin/env python3
"""
Sistema de Backup Robusto e Infalible para Base de Datos Vehicular
Previene pérdida de datos con múltiples capas de protección
"""

import os
import sqlite3
import json
import csv
import shutil
import zipfile
from datetime import datetime, timedelta
import logging
import hashlib
import pandas as pd

logger = logging.getLogger(__name__)

class DatabaseBackupManager:
    """Gestor de backups robusto con múltiples formatos y verificaciones"""
    
    def __init__(self, db_path="/home/user/webapp/vehicular_system.db"):
        self.db_path = db_path
        self.backup_dir = "/home/user/webapp/backups"
        self.ensure_backup_directory()
        
    def ensure_backup_directory(self):
        """Crear directorio de backups si no existe"""
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(f"{self.backup_dir}/automatic", exist_ok=True)
        os.makedirs(f"{self.backup_dir}/manual", exist_ok=True)
        os.makedirs(f"{self.backup_dir}/export", exist_ok=True)
        
    def get_database_stats(self):
        """Obtener estadísticas de la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Contar registros por tabla
            tables = ['vehiculos', 'mantenimientos', 'combustible', 'revisiones', 'polizas', 'rtv', 'bitacora']
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[table] = cursor.fetchone()[0]
                except sqlite3.Error:
                    stats[table] = 0
            
            # Información de la base de datos
            stats['db_size'] = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            stats['last_modified'] = datetime.fromtimestamp(
                os.path.getmtime(self.db_path)
            ).isoformat() if os.path.exists(self.db_path) else None
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de DB: {e}")
            return {}
    
    def create_full_backup(self, backup_type="manual", include_export=True):
        """Crear backup completo con múltiples formatos"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"vehicular_backup_{timestamp}"
        
        if backup_type == "automatic":
            backup_folder = f"{self.backup_dir}/automatic/{backup_name}"
        else:
            backup_folder = f"{self.backup_dir}/manual/{backup_name}"
            
        os.makedirs(backup_folder, exist_ok=True)
        
        backup_info = {
            "timestamp": timestamp,
            "backup_type": backup_type,
            "created_at": datetime.now().isoformat(),
            "stats_before": self.get_database_stats()
        }
        
        try:
            # 1. BACKUP COMPLETO DE SQLITE (.db)
            db_backup_path = f"{backup_folder}/{backup_name}.db"
            shutil.copy2(self.db_path, db_backup_path)
            backup_info["sqlite_backup"] = db_backup_path
            
            # 2. DUMP SQL (.sql)
            sql_backup_path = f"{backup_folder}/{backup_name}.sql"
            self.create_sql_dump(sql_backup_path)
            backup_info["sql_dump"] = sql_backup_path
            
            # 3. EXPORT JSON (legible y portable)
            if include_export:
                json_backup_path = f"{backup_folder}/{backup_name}.json"
                self.export_to_json(json_backup_path)
                backup_info["json_export"] = json_backup_path
                
                # 4. EXPORT CSV (Excel compatible)
                csv_folder = f"{backup_folder}/csv_export"
                self.export_to_csv(csv_folder)
                backup_info["csv_export"] = csv_folder
            
            # 5. VERIFICACIÓN DE INTEGRIDAD
            backup_info["integrity_check"] = self.verify_backup_integrity(db_backup_path)
            
            # 6. INFORMACIÓN DEL BACKUP
            info_path = f"{backup_folder}/backup_info.json"
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            # 7. CREAR ZIP COMPRIMIDO
            zip_path = f"{backup_folder}.zip"
            self.create_backup_zip(backup_folder, zip_path)
            backup_info["zip_backup"] = zip_path
            
            logger.info(f"✅ Backup completo creado: {backup_name}")
            return backup_info
            
        except Exception as e:
            logger.error(f"❌ Error creando backup: {e}")
            return {"error": str(e)}
    
    def create_sql_dump(self, output_path):
        """Crear dump SQL completo de la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                # Header del archivo SQL
                f.write("-- Backup SQL Sistema Vehicular\n")
                f.write(f"-- Creado: {datetime.now().isoformat()}\n")
                f.write("-- IMPORTANTE: Este archivo contiene TODOS los datos\n\n")
                
                # Dump completo
                for line in conn.iterdump():
                    f.write(f"{line}\n")
            
            conn.close()
            logger.info(f"✅ SQL dump creado: {output_path}")
            
        except Exception as e:
            logger.error(f"❌ Error creando SQL dump: {e}")
            raise
    
    def export_to_json(self, output_path):
        """Exportar toda la base de datos a JSON legible"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
            
            export_data = {
                "metadata": {
                    "export_date": datetime.now().isoformat(),
                    "database_stats": self.get_database_stats()
                },
                "tables": {}
            }
            
            # Exportar cada tabla
            tables = ['vehiculos', 'mantenimientos', 'combustible', 'revisiones', 'polizas', 'rtv', 'bitacora']
            
            for table in tables:
                try:
                    cursor = conn.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    
                    # Convertir rows a dict
                    export_data["tables"][table] = [
                        dict(row) for row in rows
                    ]
                    
                except sqlite3.Error as e:
                    logger.warning(f"⚠️ Error exportando tabla {table}: {e}")
                    export_data["tables"][table] = []
            
            # Guardar JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            conn.close()
            logger.info(f"✅ Export JSON creado: {output_path}")
            
        except Exception as e:
            logger.error(f"❌ Error exportando JSON: {e}")
            raise
    
    def export_to_csv(self, output_folder):
        """Exportar cada tabla a CSV separado"""
        try:
            os.makedirs(output_folder, exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            
            tables = ['vehiculos', 'mantenimientos', 'combustible', 'revisiones', 'polizas', 'rtv', 'bitacora']
            
            for table in tables:
                try:
                    # Usar pandas para mejor manejo de CSV
                    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                    csv_path = f"{output_folder}/{table}.csv"
                    df.to_csv(csv_path, index=False, encoding='utf-8')
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error exportando {table} a CSV: {e}")
            
            conn.close()
            logger.info(f"✅ CSV exports creados en: {output_folder}")
            
        except Exception as e:
            logger.error(f"❌ Error exportando CSV: {e}")
            raise
    
    def verify_backup_integrity(self, backup_db_path):
        """Verificar integridad del backup"""
        try:
            # Verificar que el archivo existe y no está corrupto
            if not os.path.exists(backup_db_path):
                return {"valid": False, "error": "Archivo de backup no encontrado"}
            
            # Intentar conectar a la base de datos
            conn = sqlite3.connect(backup_db_path)
            cursor = conn.cursor()
            
            # Verificar integridad de SQLite
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            if integrity_result == "ok":
                # Contar registros
                stats = {}
                tables = ['vehiculos', 'mantenimientos', 'combustible', 'revisiones', 'polizas', 'rtv', 'bitacora']
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        stats[table] = cursor.fetchone()[0]
                    except:
                        stats[table] = 0
                
                conn.close()
                
                return {
                    "valid": True,
                    "integrity": "ok",
                    "stats": stats,
                    "size": os.path.getsize(backup_db_path)
                }
            else:
                conn.close()
                return {"valid": False, "error": f"Integrity check failed: {integrity_result}"}
                
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def create_backup_zip(self, folder_path, zip_path):
        """Crear archivo ZIP del backup"""
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, folder_path)
                        zipf.write(file_path, arcname)
            
            logger.info(f"✅ ZIP backup creado: {zip_path}")
            
        except Exception as e:
            logger.error(f"❌ Error creando ZIP: {e}")
            raise
    
    def list_backups(self):
        """Listar todos los backups disponibles"""
        backups = {"manual": [], "automatic": []}
        
        for backup_type in ["manual", "automatic"]:
            backup_path = f"{self.backup_dir}/{backup_type}"
            
            if os.path.exists(backup_path):
                for item in os.listdir(backup_path):
                    item_path = os.path.join(backup_path, item)
                    
                    if os.path.isdir(item_path):
                        # Leer información del backup
                        info_file = os.path.join(item_path, "backup_info.json")
                        if os.path.exists(info_file):
                            try:
                                with open(info_file, 'r', encoding='utf-8') as f:
                                    backup_info = json.load(f)
                                    backup_info["folder"] = item_path
                                    backups[backup_type].append(backup_info)
                            except:
                                pass
        
        return backups
    
    def restore_from_backup(self, backup_folder):
        """Restaurar base de datos desde backup"""
        try:
            # Buscar archivo .db en el backup
            db_file = None
            for file in os.listdir(backup_folder):
                if file.endswith('.db'):
                    db_file = os.path.join(backup_folder, file)
                    break
            
            if not db_file:
                return {"success": False, "error": "No se encontró archivo .db en el backup"}
            
            # Verificar integridad antes de restaurar
            integrity = self.verify_backup_integrity(db_file)
            if not integrity.get("valid"):
                return {"success": False, "error": f"Backup corrupto: {integrity.get('error')}"}
            
            # Crear backup de la DB actual antes de restaurar
            current_backup = self.create_full_backup("automatic")
            
            # Restaurar
            shutil.copy2(db_file, self.db_path)
            
            return {
                "success": True,
                "restored_from": db_file,
                "previous_backup": current_backup,
                "stats": integrity.get("stats")
            }
            
        except Exception as e:
            logger.error(f"❌ Error restaurando backup: {e}")
            return {"success": False, "error": str(e)}
    
    def cleanup_old_backups(self, days_to_keep=30):
        """Limpiar backups antiguos automáticos"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            automatic_path = f"{self.backup_dir}/automatic"
            if os.path.exists(automatic_path):
                for item in os.listdir(automatic_path):
                    item_path = os.path.join(automatic_path, item)
                    
                    # Verificar fecha de creación
                    if os.path.isdir(item_path):
                        created_time = datetime.fromtimestamp(os.path.getctime(item_path))
                        
                        if created_time < cutoff_date:
                            shutil.rmtree(item_path)
                            deleted_count += 1
                    
                    elif item.endswith('.zip'):
                        created_time = datetime.fromtimestamp(os.path.getctime(item_path))
                        
                        if created_time < cutoff_date:
                            os.remove(item_path)
                            deleted_count += 1
            
            logger.info(f"✅ Limpieza completada: {deleted_count} backups eliminados")
            return {"deleted_count": deleted_count}
            
        except Exception as e:
            logger.error(f"❌ Error en limpieza: {e}")
            return {"error": str(e)}

# Función de utilidad para backup rápido
def create_emergency_backup():
    """Crear backup de emergencia rápido"""
    manager = DatabaseBackupManager()
    return manager.create_full_backup("manual")

def export_database_now():
    """Exportar base de datos inmediatamente en todos los formatos"""
    manager = DatabaseBackupManager()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_folder = f"{manager.backup_dir}/export/export_{timestamp}"
    os.makedirs(export_folder, exist_ok=True)
    
    try:
        # JSON Export
        json_path = f"{export_folder}/vehicular_complete_{timestamp}.json"
        manager.export_to_json(json_path)
        
        # CSV Export
        csv_folder = f"{export_folder}/csv_tables"
        manager.export_to_csv(csv_folder)
        
        # SQL Dump
        sql_path = f"{export_folder}/vehicular_dump_{timestamp}.sql"
        manager.create_sql_dump(sql_path)
        
        # DB Copy
        db_path = f"{export_folder}/vehicular_backup_{timestamp}.db"
        shutil.copy2(manager.db_path, db_path)
        
        # ZIP todo
        zip_path = f"{export_folder}.zip"
        manager.create_backup_zip(export_folder, zip_path)
        
        return {
            "success": True,
            "export_folder": export_folder,
            "files": {
                "json": json_path,
                "csv_folder": csv_folder,
                "sql": sql_path,
                "database": db_path,
                "zip": zip_path
            },
            "stats": manager.get_database_stats()
        }
        
    except Exception as e:
        logger.error(f"❌ Error en export: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Test del sistema de backup
    print("🔍 Probando sistema de backup...")
    
    manager = DatabaseBackupManager()
    
    # Estadísticas actuales
    stats = manager.get_database_stats()
    print("📊 Estadísticas actuales:")
    for table, count in stats.items():
        print(f"  {table}: {count}")
    
    # Crear backup de prueba
    print("\n🔄 Creando backup de prueba...")
    result = manager.create_full_backup("manual")
    
    if "error" not in result:
        print("✅ Backup creado exitosamente")
        print(f"📁 Ubicación: {result.get('zip_backup', 'N/A')}")
    else:
        print(f"❌ Error: {result['error']}")