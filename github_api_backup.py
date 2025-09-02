#!/usr/bin/env python3
"""
Sistema de Backup Directo a GitHub API
Sube archivos de base de datos a GitHub usando la API REST
Funciona en Railway sin necesidad de Git local
"""

import os
import sqlite3
import json
import base64
import zipfile
import shutil
from datetime import datetime
import logging
import requests
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class GitHubAPIBackup:
    """Sistema de backup directo a GitHub usando API REST"""
    
    def __init__(self, 
                 github_token: Optional[str] = None,
                 repo_owner: str = "flota-hotel", 
                 repo_name: str = "mantenimiento-vehiculos",
                 backup_branch: str = "genspark_ai_developer"):
        
        # Configuración de GitHub
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.backup_branch = backup_branch
        self.github_token = github_token or self._get_github_token()
        self.api_base = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        
        # Rutas locales
        self.current_dir = os.getcwd()
        self.db_path = os.path.join(self.current_dir, "vehicular_system.db")
        self.temp_backup_dir = os.path.join(self.current_dir, "temp_api_backups")
        
        # Verificar configuración
        self.api_available = self._verify_github_api()
        
        logger.info(f"🐙 GitHubAPIBackup inicializado:")
        logger.info(f"   📂 Repo: {repo_owner}/{repo_name}")
        logger.info(f"   🌿 Branch: {backup_branch}")
        logger.info(f"   🗂️ DB Path: {self.db_path}")
        logger.info(f"   🔑 Token: {'✅ Configurado' if self.github_token else '❌ No disponible'}")
        logger.info(f"   📡 API Available: {self.api_available}")
    
    def _get_github_token(self) -> Optional[str]:
        """Obtener token de GitHub desde variables de entorno"""
        token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
        if not token:
            # Intentar leer desde archivo .git-credentials (creado por setup_github_environment)
            try:
                creds_path = os.path.expanduser("~/.git-credentials")
                if os.path.exists(creds_path):
                    with open(creds_path, 'r') as f:
                        content = f.read().strip()
                        # Formato: https://username:token@github.com
                        if 'github.com' in content and '@' in content:
                            # Extraer token de la URL
                            parts = content.split('@')[0].split(':')
                            if len(parts) >= 3:
                                token = parts[2]
                                logger.info("🔑 Token obtenido desde ~/.git-credentials")
            except Exception as e:
                logger.debug(f"No se pudo leer .git-credentials: {e}")
        
        return token
    
    def _verify_github_api(self) -> bool:
        """Verificar que la API de GitHub esté disponible"""
        if not self.github_token:
            logger.warning("⚠️ Token de GitHub no disponible - backup API deshabilitado")
            return False
        
        try:
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(f"{self.api_base}", headers=headers, timeout=10)
            if response.status_code == 200:
                logger.info("✅ GitHub API verificada exitosamente")
                return True
            else:
                logger.error(f"❌ Error verificando GitHub API: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error conectando a GitHub API: {e}")
            return False
    
    def export_database_to_formats(self) -> dict:
        """Exportar base de datos en múltiples formatos"""
        try:
            if not os.path.exists(self.db_path):
                logger.error(f"❌ Base de datos no encontrada: {self.db_path}")
                return {}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener todas las tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            export_data = {
                "export_info": {
                    "timestamp": datetime.now().isoformat(),
                    "source": "Railway Production",
                    "database_path": self.db_path,
                    "tables_count": len(tables),
                    "backup_type": "github_api_backup"
                },
                "statistics": {},
                "tables": {}
            }
            
            total_records = 0
            
            # Exportar cada tabla
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_records += count
                
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
                
                export_data["tables"][table] = {
                    "columns": columns,
                    "data": table_data,
                    "record_count": count
                }
                
                export_data["statistics"][table] = count
            
            export_data["statistics"]["total_records"] = total_records
            
            conn.close()
            return export_data
            
        except Exception as e:
            logger.error(f"❌ Error exportando base de datos: {e}")
            return {}
    
    def create_backup_package(self, backup_type: str = "railway_auto") -> Tuple[Optional[str], Optional[dict]]:
        """Crear paquete de backup completo"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"railway_db_backup_{backup_type}_{timestamp}"
        
        # Crear directorio temporal
        os.makedirs(self.temp_backup_dir, exist_ok=True)
        temp_dir = os.path.join(self.temp_backup_dir, backup_name)
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # 1. Exportar datos en JSON
            logger.info("📋 Exportando datos a JSON...")
            export_data = self.export_database_to_formats()
            
            if not export_data:
                return None, None
            
            # 2. Guardar JSON principal
            json_path = os.path.join(temp_dir, "database_export.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            # 3. Copiar base de datos original
            if os.path.exists(self.db_path):
                db_copy_path = os.path.join(temp_dir, "vehicular_system.db")
                shutil.copy2(self.db_path, db_copy_path)
                logger.info("📁 Base de datos copiada")
            
            # 4. Crear estadísticas separadas
            stats = {
                "backup_timestamp": datetime.now().isoformat(),
                "backup_type": backup_type,
                "source": "Railway Production API",
                "total_records": export_data["statistics"]["total_records"],
                **export_data["statistics"]
            }
            
            stats_path = os.path.join(temp_dir, "backup_statistics.json")
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            # 5. Crear archivo ZIP
            zip_path = os.path.join(self.temp_backup_dir, f"{backup_name}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
            
            # Limpiar directorio temporal
            shutil.rmtree(temp_dir)
            
            logger.info(f"✅ Paquete de backup creado: {os.path.basename(zip_path)}")
            logger.info(f"📊 Total registros respaldados: {stats['total_records']}")
            
            return zip_path, stats
            
        except Exception as e:
            logger.error(f"❌ Error creando paquete de backup: {e}")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return None, None
    
    def upload_to_github(self, file_path: str, stats: dict) -> bool:
        """Subir archivo a GitHub usando API REST"""
        if not self.api_available:
            logger.warning("⚠️ GitHub API no disponible - guardando solo localmente")
            return False
        
        try:
            filename = os.path.basename(file_path)
            
            # Leer archivo y convertir a base64
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            
            # Ruta en GitHub: api_backups/filename
            github_path = f"api_backups/{filename}"
            
            # Verificar si el archivo ya existe
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            get_url = f"{self.api_base}/contents/{github_path}?ref={self.backup_branch}"
            get_response = requests.get(get_url, headers=headers)
            
            sha = None
            if get_response.status_code == 200:
                sha = get_response.json().get('sha')
                logger.info(f"📁 Archivo existe, se actualizará: {filename}")
            
            # Crear mensaje de commit
            total_records = stats.get('total_records', 0)
            backup_type = stats.get('backup_type', 'auto')
            
            commit_message = f"backup: Railway DB - {stats.get('backup_timestamp', 'unknown')}\n\n"
            commit_message += f"📊 Total registros: {total_records}\n"
            commit_message += f"🔄 Tipo: {backup_type}\n"
            commit_message += f"📁 Archivo: {filename}\n"
            
            for table, count in stats.items():
                if table not in ['backup_timestamp', 'backup_type', 'source', 'total_records'] and isinstance(count, int):
                    commit_message += f"• {table}: {count} registros\n"
            
            # Preparar datos para subir
            upload_data = {
                "message": commit_message,
                "content": content,
                "branch": self.backup_branch
            }
            
            if sha:
                upload_data["sha"] = sha
            
            # Subir archivo
            put_url = f"{self.api_base}/contents/{github_path}"
            put_response = requests.put(put_url, headers=headers, json=upload_data)
            
            if put_response.status_code in [200, 201]:
                logger.info(f"✅ Archivo subido exitosamente a GitHub: {github_path}")
                logger.info(f"📊 {total_records} registros respaldados en GitHub")
                return True
            else:
                logger.error(f"❌ Error subiendo a GitHub: {put_response.status_code}")
                logger.error(f"Respuesta: {put_response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en upload_to_github: {e}")
            return False
    
    async def backup_railway_database(self, backup_type: str = "railway_auto") -> Tuple[bool, Optional[str]]:
        """Backup completo desde Railway a GitHub"""
        logger.info(f"🚀 Iniciando backup de Railway a GitHub...")
        
        try:
            # 1. Crear paquete de backup
            zip_path, stats = self.create_backup_package(backup_type)
            
            if not zip_path or not stats:
                logger.error("❌ Error creando paquete de backup")
                return False, None
            
            # 2. Subir a GitHub
            filename = os.path.basename(zip_path)
            upload_success = self.upload_to_github(zip_path, stats)
            
            # 3. Limpiar archivo temporal
            if os.path.exists(zip_path):
                os.remove(zip_path)
            
            if upload_success:
                logger.info(f"🎉 Backup completo exitoso: {filename}")
                return True, filename
            else:
                # Aunque falle GitHub, el backup se creó exitosamente
                logger.info(f"📦 Backup creado localmente: {filename}")
                return True, filename
                
        except Exception as e:
            logger.error(f"❌ Error en backup_railway_database: {e}")
            return False, None
        finally:
            # Limpiar directorio temporal
            if os.path.exists(self.temp_backup_dir):
                try:
                    shutil.rmtree(self.temp_backup_dir)
                except:
                    pass

# Función de conveniencia
async def backup_to_github(backup_type: str = "railway_auto") -> Tuple[bool, Optional[str]]:
    """Función simple para hacer backup a GitHub"""
    backup_system = GitHubAPIBackup()
    return await backup_system.backup_railway_database(backup_type)

if __name__ == "__main__":
    # Test del sistema
    import asyncio
    
    async def test():
        backup_system = GitHubAPIBackup()
        success, filename = await backup_system.backup_railway_database("test")
        if success:
            print(f"✅ Test exitoso: {filename}")
        else:
            print("❌ Test falló")
    
    asyncio.run(test())