#!/usr/bin/env python3
"""
Servicio de Backup Automático a GitHub
Ejecuta backups periódicos de la base de datos
"""

import time
import schedule
import logging
from datetime import datetime
import sys
import os

# Agregar el directorio actual al path para importar módulos locales
sys.path.append('/home/user/webapp')

from github_backup_system import GitHubBackupSystem

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/user/webapp/logs/github_backup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AutoBackupService:
    """Servicio de backup automático"""
    
    def __init__(self):
        self.backup_system = GitHubBackupSystem()
        self.running = False
        
    def daily_backup(self):
        """Ejecutar backup diario"""
        logger.info("Iniciando backup diario automático...")
        try:
            success, filename = self.backup_system.create_and_upload_backup("daily")
            if success:
                logger.info(f"✅ Backup diario completado: {filename}")
                
                # Limpiar backups antiguos
                cleaned = self.backup_system.cleanup_old_backups(keep_days=30)
                if cleaned > 0:
                    logger.info(f"🧹 Limpieza completada: {cleaned} backups antiguos eliminados")
            else:
                logger.error("❌ Error en backup diario")
        except Exception as e:
            logger.error(f"Error ejecutando backup diario: {e}")
    
    def hourly_backup(self):
        """Ejecutar backup cada hora (solo en horario laboral)"""
        current_hour = datetime.now().hour
        
        # Solo hacer backup automático en horario laboral (8 AM - 8 PM)
        if 8 <= current_hour <= 20:
            logger.info("Iniciando backup por hora...")
            try:
                success, filename = self.backup_system.create_and_upload_backup("hourly")
                if success:
                    logger.info(f"✅ Backup por hora completado: {filename}")
                else:
                    logger.error("❌ Error en backup por hora")
            except Exception as e:
                logger.error(f"Error ejecutando backup por hora: {e}")
        else:
            logger.info(f"Fuera de horario laboral ({current_hour}:00), saltando backup automático")
    
    def setup_schedule(self):
        """Configurar horarios de backup"""
        # Backup diario a las 2 AM
        schedule.every().day.at("02:00").do(self.daily_backup)
        
        # Backup cada hora en horario laboral
        schedule.every().hour.do(self.hourly_backup)
        
        logger.info("✅ Horarios de backup configurados:")
        logger.info("📅 Backup diario: 02:00 AM")
        logger.info("⏰ Backup por hora: 8 AM - 8 PM")
    
    def run(self):
        """Ejecutar el servicio de backup"""
        logger.info("🚀 Iniciando servicio de backup automático a GitHub...")
        
        # Hacer un backup inicial
        logger.info("Ejecutando backup inicial...")
        self.backup_system.create_and_upload_backup("initial")
        
        # Configurar horarios
        self.setup_schedule()
        
        self.running = True
        logger.info("✅ Servicio de backup iniciado correctamente")
        
        # Loop principal
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Revisar cada minuto
            except KeyboardInterrupt:
                logger.info("🛑 Deteniendo servicio de backup...")
                self.running = False
            except Exception as e:
                logger.error(f"Error en loop principal: {e}")
                time.sleep(60)
    
    def stop(self):
        """Detener el servicio"""
        self.running = False
        logger.info("Servicio de backup detenido")

def run_manual_backup():
    """Ejecutar backup manual inmediato"""
    backup_service = AutoBackupService()
    logger.info("🔧 Ejecutando backup manual...")
    
    success, filename = backup_service.backup_system.create_and_upload_backup("manual")
    
    if success:
        print(f"✅ Backup manual completado exitosamente: {filename}")
        logger.info(f"Backup manual exitoso: {filename}")
        return True
    else:
        print("❌ Error ejecutando backup manual")
        logger.error("Error en backup manual")
        return False

if __name__ == "__main__":
    # Verificar argumentos de línea de comandos
    if len(sys.argv) > 1:
        if sys.argv[1] == "manual":
            # Ejecutar backup manual
            run_manual_backup()
        elif sys.argv[1] == "daemon":
            # Ejecutar como servicio daemon
            service = AutoBackupService()
            service.run()
        else:
            print("Uso: python auto_github_backup.py [manual|daemon]")
    else:
        # Por defecto, ejecutar backup manual
        run_manual_backup()