#!/usr/bin/env python3
"""
Script de Protección de Datos - NUNCA PERMITIR PÉRDIDA DE DATOS
Este script DEBE ejecutarse antes de cualquier modificación del sistema
"""

import os
import sqlite3
import shutil
import json
from datetime import datetime

def backup_database_immediately():
    """Crear backup inmediato de la base de datos actual"""
    db_path = "/home/user/webapp/vehicular_system.db"
    
    if not os.path.exists(db_path):
        print("⚠️ ALERTA: Base de datos no encontrada!")
        return False
    
    # Crear backup con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"/home/user/webapp/vehicular_system_PROTECTED_{timestamp}.db"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup protectivo creado: {backup_path}")
        
        # Verificar que el backup es válido
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        
        # Contar registros importantes
        cursor.execute("SELECT COUNT(*) FROM vehiculos")
        vehiculos_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM mantenimientos")
        mantenimientos_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM combustible") 
        combustible_count = cursor.fetchone()[0]
        
        conn.close()
        
        stats = {
            "timestamp": datetime.now().isoformat(),
            "backup_path": backup_path,
            "vehiculos": vehiculos_count,
            "mantenimientos": mantenimientos_count,
            "combustible": combustible_count,
            "status": "PROTEGIDO"
        }
        
        # Guardar estadísticas
        stats_path = backup_path.replace('.db', '_stats.json')
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"📊 Datos protegidos: {vehiculos_count} vehículos, {mantenimientos_count} mantenimientos, {combustible_count} combustible")
        return True, stats
        
    except Exception as e:
        print(f"❌ ERROR creando backup: {e}")
        return False, None

def verify_data_integrity():
    """Verificar integridad actual de los datos"""
    db_path = "/home/user/webapp/vehicular_system.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tablas principales
        cursor.execute("SELECT COUNT(*) FROM vehiculos")
        vehiculos = cursor.fetchone()[0]
        
        cursor.execute("SELECT placa, marca, modelo FROM vehiculos")
        vehiculos_list = cursor.fetchall()
        
        cursor.execute("SELECT COUNT(*) FROM mantenimientos")
        mantenimientos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM combustible")
        combustible = cursor.fetchone()[0]
        
        conn.close()
        
        print("\n📋 ESTADO ACTUAL DE LA BASE DE DATOS:")
        print(f"🚗 Vehículos: {vehiculos}")
        for placa, marca, modelo in vehiculos_list:
            print(f"   - {placa}: {marca} {modelo}")
        print(f"🔧 Mantenimientos: {mantenimientos}")
        print(f"⛽ Combustible: {combustible}")
        
        return {
            "vehiculos": vehiculos,
            "vehiculos_list": vehiculos_list,
            "mantenimientos": mantenimientos,
            "combustible": combustible
        }
        
    except Exception as e:
        print(f"❌ ERROR verificando integridad: {e}")
        return None

def protect_before_changes():
    """Protección completa antes de cambios"""
    print("\n🛡️ INICIANDO PROTECCIÓN DE DATOS...")
    
    # 1. Verificar estado actual
    current_state = verify_data_integrity()
    
    if not current_state:
        print("❌ ABORTAR: No se puede verificar estado actual")
        return False
    
    # 2. Crear backup protectivo
    success, backup_info = backup_database_immediately()
    
    if not success:
        print("❌ ABORTAR: No se pudo crear backup protectivo")
        return False
    
    # 3. Advertencia final
    print("\n⚠️ IMPORTANTE:")
    print("- Los datos actuales están RESPALDADOS")  
    print("- Cualquier pérdida puede restaurarse")
    print("- NUNCA hacer cambios que puedan sobrescribir la DB")
    
    return True

if __name__ == "__main__":
    protect_before_changes()