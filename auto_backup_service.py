#!/usr/bin/env python3
"""
Servicio Automático de Backup - Protección Continua
Ejecuta backups automáticos cada hora para prevenir pérdida de datos
"""

import schedule
import time
import logging
from datetime import datetime
from backup_manager import DatabaseBackupManager
import threading

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/user/webapp/backup_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoBackupService:
    """Servicio de backup automático con múltiples horarios"""
    
    def __init__(self):
        self.manager = DatabaseBackupManager()
        self.running = False
        
    def hourly_backup(self):
        """Backup cada hora (solo DB y SQL)"""
        try:
            logger.info("🔄 Iniciando backup automático horario...")
            
            # Backup ligero (solo DB y SQL, sin CSV)
            result = self.manager.create_full_backup("automatic", include_export=False)
            
            if "error" not in result:
                stats = result.get("stats_before", {})
                total_records = sum([count for count in stats.values() if isinstance(count, int)])
                
                logger.info(f"✅ Backup horario completado - {total_records} registros protegidos")
                
                # Limpiar backups antiguos (mantener 7 días)
                self.manager.cleanup_old_backups(days_to_keep=7)
                
            else:
                logger.error(f"❌ Error en backup horario: {result['error']}")
                
        except Exception as e:
            logger.error(f"❌ Excepción en backup horario: {e}")
    
    def daily_backup(self):
        """Backup diario completo (con exports)"""
        try:
            logger.info("🔄 Iniciando backup diario completo...")
            
            # Backup completo con todos los formatos
            result = self.manager.create_full_backup("automatic", include_export=True)
            
            if "error" not in result:
                stats = result.get("stats_before", {})
                logger.info("✅ Backup diario completo - Todos los formatos creados")
                
                # Mostrar estadísticas
                for table, count in stats.items():
                    if isinstance(count, int):
                        logger.info(f"  📊 {table}: {count} registros")
                        
            else:
                logger.error(f"❌ Error en backup diario: {result['error']}")
                
        except Exception as e:
            logger.error(f"❌ Excepción en backup diario: {e}")
    
    def emergency_monitor(self):
        """Monitor de emergencia - verifica integridad cada 15 min"""
        try:
            stats = self.manager.get_database_stats()
            
            # Verificar que las tablas principales tengan datos
            critical_tables = ['vehiculos', 'mantenimientos']
            
            for table in critical_tables:
                count = stats.get(table, 0)
                
                if count == 0:
                    logger.warning(f"⚠️ ALERTA: Tabla {table} está vacía!")
                    # Crear backup de emergencia inmediato
                    self.manager.create_full_backup("automatic")
            
        except Exception as e:
            logger.error(f"❌ Error en monitor de emergencia: {e}")
    
    def start_service(self):
        """Iniciar servicio de backup automático"""
        logger.info("🚀 Iniciando servicio de backup automático...")
        
        # Programar tareas
        schedule.every().hour.do(self.hourly_backup)
        schedule.every().day.at("02:00").do(self.daily_backup)  # 2:00 AM diario
        schedule.every(15).minutes.do(self.emergency_monitor)
        
        # Crear backup inicial
        logger.info("📋 Creando backup inicial del servicio...")
        self.hourly_backup()
        
        self.running = True
        logger.info("✅ Servicio de backup iniciado correctamente")
        
        # Loop principal
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
                
        except KeyboardInterrupt:
            logger.info("🛑 Servicio de backup detenido por usuario")
        except Exception as e:
            logger.error(f"❌ Error en servicio de backup: {e}")
        finally:
            self.running = False
    
    def stop_service(self):
        """Detener servicio"""
        logger.info("🛑 Deteniendo servicio de backup...")
        self.running = False

def run_backup_service():
    """Ejecutar servicio en hilo separado"""
    service = AutoBackupService()
    service.start_service()

if __name__ == "__main__":
    print("🔧 SERVICIO DE BACKUP AUTOMÁTICO")
    print("Protección continua contra pérdida de datos")
    print("=" * 50)
    
    service = AutoBackupService()
    
    try:
        service.start_service()
    except KeyboardInterrupt:
        print("\n🛑 Servicio detenido")
    except Exception as e:
        print(f"❌ Error: {e}")