#!/usr/bin/env python3
"""
Sistema de Backup Automático a GitHub para Base de Datos Vehicular
Mantiene copias seguras de todos los datos en el repositorio
"""

import os
import sqlite3
import json
import base64
import subprocess
import zipfile
import shutil
import csv
from datetime import datetime, timedelta
import logging
import hashlib

logger = logging.getLogger(__name__)

class GitHubBackupSystem:
    """Sistema de backup automático que guarda datos en GitHub"""
    
    def __init__(self, db_path=None):
        # Obtener directorio de trabajo actual
        current_dir = os.getcwd()
        # En Railway, usar la ruta actual, en desarrollo usar webapp
        if db_path is None:
            self.db_path = os.path.join(current_dir, "vehicular_system.db")
        else:
            self.db_path = db_path
            
        self.backup_dir = os.path.join(current_dir, "backups")
        self.github_backup_dir = os.path.join(current_dir, "github_backups")
        self.repo_path = current_dir
        self.ensure_directories()
        
        # Log para debugging
        logger.info(f"📍 GitHubBackupSystem inicializado:")
        logger.info(f"   🗂️ DB Path: {self.db_path}")
        logger.info(f"   📁 Backup Dir: {self.backup_dir}")
        logger.info(f"   🐙 GitHub Dir: {self.github_backup_dir}")
        logger.info(f"   📂 Repo Path: {self.repo_path}")
        logger.info(f"   ✅ DB Exists: {os.path.exists(self.db_path)}")
        
    def ensure_directories(self):
        """Crear directorios necesarios"""
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.github_backup_dir, exist_ok=True)
        os.makedirs(f"{self.github_backup_dir}/automatic", exist_ok=True)
        os.makedirs(f"{self.github_backup_dir}/manual", exist_ok=True)
        
    def get_database_stats(self):
        """Obtener estadísticas actuales de la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Contar registros por tabla
            tables = ['vehiculos', 'mantenimientos', 'combustible', 'revisiones', 'polizas', 'rtv', 'bitacora']
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[table] = cursor.fetchone()[0]
                except sqlite3.Error:
                    stats[table] = 0
                    
            conn.close()
            
            stats['backup_timestamp'] = timestamp
            # Calcular total solo de valores numéricos
            numeric_stats = {k: v for k, v in stats.items() if isinstance(v, int)}
            stats['total_records'] = sum(numeric_stats.values())
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {"error": str(e), "backup_timestamp": datetime.now().isoformat()}
    
    def export_database_to_json(self):
        """Exportar toda la base de datos a JSON"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Obtener todas las tablas
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            database_export = {
                "export_info": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0",
                    "database_path": self.db_path,
                    "tables_count": len(tables)
                },
                "tables": {}
            }
            
            # Exportar cada tabla
            for table in tables:
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                
                # Obtener nombres de columnas
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Convertir a lista de diccionarios
                table_data = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        row_dict[columns[i]] = value
                    table_data.append(row_dict)
                
                database_export["tables"][table] = {
                    "columns": columns,
                    "data": table_data,
                    "record_count": len(table_data)
                }
            
            conn.close()
            return database_export
            
        except Exception as e:
            logger.error(f"Error exportando base de datos: {e}")
            return {"error": str(e)}
    
    def create_backup_package(self, backup_type="automatic"):
        """Crear paquete completo de backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"vehicular_backup_{backup_type}_{timestamp}"
        
        # Directorio temporal para el backup
        temp_backup_dir = f"{self.github_backup_dir}/temp_{backup_name}"
        os.makedirs(temp_backup_dir, exist_ok=True)
        
        try:
            # 1. Copiar base de datos original
            db_backup_path = f"{temp_backup_dir}/vehicular_system.db"
            shutil.copy2(self.db_path, db_backup_path)
            
            # 2. Exportar a JSON
            database_json = self.export_database_to_json()
            json_path = f"{temp_backup_dir}/database_export.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(database_json, f, indent=2, ensure_ascii=False, default=str)
            
            # 3. Crear estadísticas
            stats = self.get_database_stats()
            stats_path = f"{temp_backup_dir}/backup_stats.json"
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            # 4. Exportar a CSV por tabla
            csv_dir = f"{temp_backup_dir}/csv_exports"
            os.makedirs(csv_dir, exist_ok=True)
            
            # Exportar cada tabla a CSV usando módulo csv nativo
            for table_name, table_info in database_json["tables"].items():
                if table_info["record_count"] > 0:
                    csv_path = f"{csv_dir}/{table_name}.csv"
                    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                        if table_info["data"]:
                            fieldnames = table_info["columns"]
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(table_info["data"])
            
            # 5. Crear archivo ZIP
            zip_path = f"{self.github_backup_dir}/{backup_name}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_backup_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_backup_dir)
                        zipf.write(file_path, arcname)
            
            # Limpiar directorio temporal
            shutil.rmtree(temp_backup_dir)
            
            return zip_path, stats
            
        except Exception as e:
            logger.error(f"Error creando paquete de backup: {e}")
            if os.path.exists(temp_backup_dir):
                shutil.rmtree(temp_backup_dir)
            return None, None
    
    def commit_backup_to_github(self, backup_path, stats, backup_type="automatic"):
        """Subir backup a GitHub"""
        try:
            # Verificar si el backup ya está en el directorio correcto
            backup_filename = os.path.basename(backup_path)
            target_dir = f"{self.repo_path}/github_backups"
            os.makedirs(target_dir, exist_ok=True)
            
            # Solo mover si no está en el directorio correcto
            if not backup_path.startswith(target_dir):
                repo_backup_path = f"{target_dir}/{backup_filename}"
                shutil.move(backup_path, repo_backup_path)
            else:
                repo_backup_path = backup_path
            
            # Crear archivo de estadísticas
            stats_filename = backup_filename.replace('.zip', '_stats.json')
            stats_path = f"{self.repo_path}/github_backups/{stats_filename}"
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            # Commit a GitHub
            os.chdir(self.repo_path)
            
            # Agregar archivos
            subprocess.run(['git', 'add', f'github_backups/{backup_filename}'], check=True)
            subprocess.run(['git', 'add', f'github_backups/{stats_filename}'], check=True)
            
            # Crear mensaje de commit informativo
            total_records = stats.get('total_records', 0)
            timestamp = stats.get('backup_timestamp', 'unknown')
            
            commit_message = f"backup: Backup automático de base de datos - {timestamp}\n\n"
            commit_message += f"📊 Estadísticas del backup:\n"
            commit_message += f"• Total de registros: {total_records}\n"
            
            for table, count in stats.items():
                if table not in ['backup_timestamp', 'total_records'] and isinstance(count, int):
                    commit_message += f"• {table.capitalize()}: {count} registros\n"
            
            commit_message += f"\n🔄 Tipo: {backup_type}\n"
            commit_message += f"📁 Archivo: {backup_filename}"
            
            # Hacer commit
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
            
            # Push al repositorio
            subprocess.run(['git', 'push', 'origin', 'genspark_ai_developer'], check=True)
            
            logger.info(f"Backup subido exitosamente a GitHub: {backup_filename}")
            return True, backup_filename
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error en comando git: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Error subiendo backup a GitHub: {e}")
            return False, None
    
    async def create_and_upload_backup(self, backup_type="automatic"):
        """Proceso completo: crear backup y subirlo a GitHub (async)"""
        logger.info(f"Iniciando backup {backup_type}...")
        
        # Verificar que la base de datos existe
        if not os.path.exists(self.db_path):
            logger.error(f"❌ Base de datos no encontrada: {self.db_path}")
            return False, None
        
        # Crear paquete de backup
        backup_path, stats = self.create_backup_package(backup_type)
        
        if not backup_path:
            logger.error("Error creando paquete de backup")
            return False, None
        
        # Subir a GitHub
        success, filename = self.commit_backup_to_github(backup_path, stats, backup_type)
        
        if success:
            logger.info(f"Backup completado exitosamente: {filename}")
            # Limpiar backup local temporal
            if os.path.exists(backup_path):
                os.remove(backup_path)
            return True, filename
        else:
            logger.error("Error subiendo backup a GitHub")
            return False, None
    
    def cleanup_old_backups(self, keep_days=7):
        """Limpiar backups antiguos (mantener solo los últimos N días)"""
        try:
            backup_files = []
            github_backups_dir = f"{self.repo_path}/github_backups"
            if not os.path.exists(github_backups_dir):
                return 0
                
            for file in os.listdir(github_backups_dir):
                if file.startswith("vehicular_backup_") and file.endswith(".zip"):
                    file_path = f"{github_backups_dir}/{file}"
                    file_time = os.path.getctime(file_path)
                    backup_files.append((file_path, file_time, file))
            
            # Ordenar por fecha
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Mantener solo los backups recientes
            cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 3600)
            old_files = []
            
            for file_path, file_time, filename in backup_files[10:]:  # Mantener al menos 10 backups
                if file_time < cutoff_time:
                    old_files.append((file_path, filename))
            
            # Eliminar archivos antiguos
            for file_path, filename in old_files:
                os.remove(file_path)
                # También eliminar archivo de estadísticas asociado
                stats_file = file_path.replace('.zip', '_stats.json')
                if os.path.exists(stats_file):
                    os.remove(stats_file)
                logger.info(f"Backup antiguo eliminado: {filename}")
            
            return len(old_files)
            
        except Exception as e:
            logger.error(f"Error limpiando backups antiguos: {e}")
            return 0

def manual_backup():
    """Función para ejecutar backup manual"""
    backup_system = GitHubBackupSystem()
    success, filename = backup_system.create_and_upload_backup("manual")
    
    if success:
        print(f"✅ Backup manual completado: {filename}")
        return True
    else:
        print("❌ Error en backup manual")
        return False

async def automatic_backup():
    """Función para ejecutar backup automático (async)"""
    backup_system = GitHubBackupSystem()
    success, filename = await backup_system.create_and_upload_backup("automatic")
    
    if success:
        print(f"✅ Backup automático completado: {filename}")
        return True
    else:
        print("❌ Error en backup automático")
        return False

if __name__ == "__main__":
    # Ejecutar backup manual si se ejecuta directamente
    manual_backup()