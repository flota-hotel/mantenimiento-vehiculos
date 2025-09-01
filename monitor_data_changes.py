#!/usr/bin/env python3
"""
Monitor de Cambios de Datos - Vigilancia Continua
Monitorea la base de datos para detectar cualquier pérdida de datos
"""

import sqlite3
import time
import json
import requests
from datetime import datetime
import os

class DataChangeMonitor:
    def __init__(self):
        self.db_path = "/home/user/webapp/vehicular_system.db" 
        self.api_url = "https://mantenimiento-vehiculos-production.up.railway.app"
        self.last_known_state = None
        self.monitoring = True
        
    def get_current_state(self):
        """Obtener estado actual de la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener todos los vehículos
            cursor.execute("SELECT placa, marca, modelo, ano, color FROM vehiculos ORDER BY placa")
            vehiculos = cursor.fetchall()
            
            # Obtener conteos de otras tablas
            cursor.execute("SELECT COUNT(*) FROM mantenimientos")
            mantenimientos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM combustible")
            combustible = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM revisiones")
            revisiones = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "vehiculos": vehiculos,
                "vehiculos_count": len(vehiculos),
                "mantenimientos_count": mantenimientos,
                "combustible_count": combustible,
                "revisiones_count": revisiones
            }
            
        except Exception as e:
            print(f"❌ Error obteniendo estado: {e}")
            return None
    
    def verify_api_consistency(self):
        """Verificar que la API devuelve los mismos datos que la DB local"""
        try:
            # Obtener datos de la API
            response = requests.get(f"{self.api_url}/vehiculos", timeout=10)
            
            if response.status_code == 200:
                api_data = response.json()
                
                if api_data.get("success"):
                    api_vehiculos = api_data.get("data", [])
                    
                    # Obtener datos locales
                    local_state = self.get_current_state()
                    
                    if local_state:
                        local_count = local_state["vehiculos_count"]
                        api_count = len(api_vehiculos)
                        
                        if local_count != api_count:
                            print(f"⚠️ INCONSISTENCIA: Local={local_count}, API={api_count}")
                            return False
                        else:
                            print(f"✅ Consistencia verificada: {local_count} vehículos")
                            return True
                    
        except Exception as e:
            print(f"⚠️ Error verificando API: {e}")
            return None
    
    def detect_data_loss(self, previous_state, current_state):
        """Detectar si se perdieron datos"""
        if not previous_state or not current_state:
            return []
        
        issues = []
        
        # Verificar vehículos
        prev_vehiculos = set(v[0] for v in previous_state["vehiculos"])  # placas
        curr_vehiculos = set(v[0] for v in current_state["vehiculos"])  # placas
        
        lost_vehiculos = prev_vehiculos - curr_vehiculos
        if lost_vehiculos:
            issues.append(f"🚨 VEHÍCULOS PERDIDOS: {list(lost_vehiculos)}")
        
        # Verificar conteos
        for key in ["mantenimientos_count", "combustible_count", "revisiones_count"]:
            if current_state[key] < previous_state[key]:
                diff = previous_state[key] - current_state[key]
                issues.append(f"🚨 PÉRDIDA EN {key.upper()}: -{diff} registros")
        
        return issues
    
    def save_state_log(self, state):
        """Guardar log del estado actual"""
        log_file = "/home/user/webapp/data_monitor_log.json"
        
        try:
            # Leer log existente
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    log_data = json.load(f)
            else:
                log_data = {"monitoring_started": datetime.now().isoformat(), "states": []}
            
            # Agregar estado actual
            log_data["states"].append(state)
            
            # Mantener solo los últimos 50 estados
            if len(log_data["states"]) > 50:
                log_data["states"] = log_data["states"][-50:]
            
            # Guardar log
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Error guardando log: {e}")
    
    def monitor_once(self):
        """Ejecutar un ciclo de monitoreo"""
        print(f"\n🔍 Monitoreando datos - {datetime.now().strftime('%H:%M:%S')}")
        
        # Obtener estado actual
        current_state = self.get_current_state()
        
        if not current_state:
            print("❌ No se pudo obtener estado actual")
            return
        
        # Verificar API
        self.verify_api_consistency()
        
        # Detectar pérdidas si hay estado previo
        if self.last_known_state:
            issues = self.detect_data_loss(self.last_known_state, current_state)
            
            if issues:
                print("🚨 ALERTA DE PÉRDIDA DE DATOS:")
                for issue in issues:
                    print(f"   {issue}")
                
                # Crear backup de emergencia
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                emergency_backup = f"/home/user/webapp/EMERGENCY_BACKUP_{timestamp}.db"
                
                try:
                    import shutil
                    shutil.copy2(self.db_path, emergency_backup)
                    print(f"💾 Backup de emergencia creado: {emergency_backup}")
                except Exception as e:
                    print(f"❌ Error creando backup de emergencia: {e}")
            else:
                print("✅ No se detectaron pérdidas de datos")
        
        # Mostrar estado actual
        print(f"📊 Estado: {current_state['vehiculos_count']} vehículos, "
              f"{current_state['mantenimientos_count']} mantenimientos, "
              f"{current_state['combustible_count']} combustible")
        
        # Guardar log
        self.save_state_log(current_state)
        
        # Actualizar estado conocido
        self.last_known_state = current_state
    
    def start_monitoring(self, interval_seconds=30):
        """Iniciar monitoreo continuo"""
        print("🛡️ Iniciando monitoreo de protección de datos...")
        
        try:
            while self.monitoring:
                self.monitor_once()
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoreo detenido por usuario")
        except Exception as e:
            print(f"\n❌ Error en monitoreo: {e}")

def test_current_data():
    """Función de prueba para verificar datos actuales"""
    monitor = DataChangeMonitor()
    monitor.monitor_once()

if __name__ == "__main__":
    # Por defecto, ejecutar una verificación simple
    test_current_data()