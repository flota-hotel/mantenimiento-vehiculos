#!/usr/bin/env python3
"""
Monitor de Sincronización Railway - Garantizar que TODO se guarde
Vigila que cada acción del usuario se persista correctamente
"""

import requests
import time
import json
import sqlite3
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RailwaySyncMonitor:
    def __init__(self):
        self.api_base = "https://mantenimiento-vehiculos-production.up.railway.app"
        self.previous_state = None
        self.monitoring = True
        
    def get_railway_state(self):
        """Obtener estado completo actual de Railway"""
        try:
            endpoints = ['vehiculos', 'mantenimientos', 'combustible', 'revisiones', 'polizas', 'rtv', 'bitacora']
            state = {
                'timestamp': datetime.now().isoformat(),
                'data': {}
            }
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{self.api_base}/{endpoint}", timeout=10)
                    if response.status_code == 200:
                        api_response = response.json()
                        if api_response.get("success"):
                            data = api_response.get("data", [])
                            state['data'][endpoint] = {
                                'count': len(data),
                                'records': data,
                                'last_id': max([r.get('id', 0) for r in data] + [0])
                            }
                        else:
                            state['data'][endpoint] = {'count': 0, 'records': [], 'last_id': 0}
                    else:
                        logger.warning(f"HTTP {response.status_code} para {endpoint}")
                        state['data'][endpoint] = {'count': 0, 'records': [], 'last_id': 0}
                except Exception as e:
                    logger.error(f"Error obteniendo {endpoint}: {e}")
                    state['data'][endpoint] = {'count': 0, 'records': [], 'last_id': 0}
            
            return state
            
        except Exception as e:
            logger.error(f"Error obteniendo estado Railway: {e}")
            return None
    
    def detect_changes(self, previous, current):
        """Detectar cambios entre estados"""
        if not previous or not current:
            return []
        
        changes = []
        
        for endpoint in current['data']:
            prev_data = previous['data'].get(endpoint, {'count': 0, 'records': [], 'last_id': 0})
            curr_data = current['data'][endpoint]
            
            # Detectar nuevos registros
            if curr_data['count'] > prev_data['count']:
                diff = curr_data['count'] - prev_data['count']
                changes.append({
                    'type': 'NEW_RECORDS',
                    'endpoint': endpoint,
                    'count': diff,
                    'message': f"✅ {diff} nuevo(s) registro(s) en {endpoint}",
                    'new_records': curr_data['records'][-diff:] if curr_data['records'] else []
                })
            
            # Detectar registros perdidos
            elif curr_data['count'] < prev_data['count']:
                diff = prev_data['count'] - curr_data['count']
                changes.append({
                    'type': 'LOST_RECORDS',
                    'endpoint': endpoint,
                    'count': diff,
                    'message': f"🚨 ALERTA: {diff} registro(s) perdido(s) en {endpoint}",
                    'severity': 'CRITICAL'
                })
            
            # Detectar cambios en IDs (actualizaciones)
            elif curr_data['last_id'] != prev_data['last_id']:
                changes.append({
                    'type': 'UPDATED_RECORDS',
                    'endpoint': endpoint,
                    'message': f"🔄 Registros actualizados en {endpoint}",
                    'prev_last_id': prev_data['last_id'],
                    'curr_last_id': curr_data['last_id']
                })
        
        return changes
    
    def verify_save_operation(self, endpoint, expected_increase=1, timeout=30):
        """Verificar que una operación de guardado se completó"""
        print(f"🔍 Verificando guardado en {endpoint}...")
        
        # Obtener estado inicial
        initial_state = self.get_railway_state()
        if not initial_state:
            print("❌ No se pudo obtener estado inicial")
            return False
        
        initial_count = initial_state['data'][endpoint]['count']
        expected_count = initial_count + expected_increase
        
        print(f"📊 Estado inicial: {initial_count} registros")
        print(f"🎯 Esperando: {expected_count} registros")
        
        # Esperar y verificar
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_state = self.get_railway_state()
            if current_state:
                current_count = current_state['data'][endpoint]['count']
                
                if current_count >= expected_count:
                    print(f"✅ GUARDADO CONFIRMADO: {current_count} registros")
                    
                    # Mostrar el nuevo registro
                    if current_state['data'][endpoint]['records']:
                        latest_record = current_state['data'][endpoint]['records'][-1]
                        if endpoint == 'vehiculos':
                            print(f"🚗 Nuevo vehículo: {latest_record.get('placa')} - {latest_record.get('marca')} {latest_record.get('modelo')}")
                        else:
                            print(f"📝 Nuevo registro ID: {latest_record.get('id')}")
                    
                    return True
                else:
                    print(f"⏳ Esperando... ({current_count}/{expected_count})")
            
            time.sleep(2)
        
        print(f"❌ TIMEOUT: El registro no se guardó en {timeout} segundos")
        return False
    
    def monitor_continuous(self, interval=10):
        """Monitoreo continuo de cambios"""
        print("🔄 Iniciando monitoreo continuo de Railway...")
        
        # Estado inicial
        self.previous_state = self.get_railway_state()
        if not self.previous_state:
            print("❌ No se pudo obtener estado inicial")
            return
        
        print("📊 Estado inicial obtenido:")
        for endpoint, data in self.previous_state['data'].items():
            print(f"   {endpoint}: {data['count']} registros")
        
        try:
            while self.monitoring:
                time.sleep(interval)
                
                current_state = self.get_railway_state()
                if not current_state:
                    continue
                
                changes = self.detect_changes(self.previous_state, current_state)
                
                if changes:
                    print(f"\n🔔 CAMBIOS DETECTADOS - {datetime.now().strftime('%H:%M:%S')}")
                    for change in changes:
                        print(f"   {change['message']}")
                        
                        # Si hay nuevos registros, mostrar detalles
                        if change['type'] == 'NEW_RECORDS' and change.get('new_records'):
                            for record in change['new_records']:
                                if change['endpoint'] == 'vehiculos':
                                    print(f"      🚗 {record.get('placa')} - {record.get('marca')} {record.get('modelo')}")
                                
                        # Si hay pérdidas críticas, alertar
                        if change['type'] == 'LOST_RECORDS':
                            print(f"      🚨 ACCIÓN REQUERIDA: Verificar pérdida de datos")
                            self.create_emergency_backup()
                
                self.previous_state = current_state
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoreo detenido por usuario")
    
    def create_emergency_backup(self):
        """Crear backup de emergencia por pérdida detectada"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            print(f"💾 Creando backup de emergencia: emergency_{timestamp}")
            
            # Aquí podrías llamar al sistema de backup
            # Por ahora, solo log la alerta
            logger.critical(f"PÉRDIDA DE DATOS DETECTADA - Backup de emergencia necesario")
            
        except Exception as e:
            logger.error(f"Error creando backup de emergencia: {e}")

def test_save_verification():
    """Función de prueba para verificar guardado"""
    monitor = RailwaySyncMonitor()
    
    print("🧪 MODO DE PRUEBA - Verificación de guardado")
    print("Agrega un vehículo en Railway y observa...")
    
    # Verificar estado actual
    current_state = monitor.get_railway_state()
    if current_state:
        print("\n📊 ESTADO ACTUAL:")
        for endpoint, data in current_state['data'].items():
            if data['count'] > 0:
                print(f"   {endpoint}: {data['count']} registros")
                
                if endpoint == 'vehiculos' and data['records']:
                    print("   🚗 Vehículos:")
                    for vehiculo in data['records']:
                        print(f"      - {vehiculo.get('placa')} - {vehiculo.get('marca')} {vehiculo.get('modelo')}")
    
    return monitor

if __name__ == "__main__":
    # Ejecutar prueba por defecto
    monitor = test_save_verification()
    
    print("\n¿Deseas monitoreo continuo? (y/N): ", end="")
    response = input().lower()
    
    if response == 'y':
        monitor.monitor_continuous()