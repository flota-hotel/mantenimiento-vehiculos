#!/usr/bin/env python3
"""
Script para agregar el vehículo AB 844 y verificar el guardado
"""

import requests
import json
import time
from datetime import datetime

def add_vehicle_ab844():
    """Agregar vehículo AB 844 con verificación completa"""
    
    api_url = "https://mantenimiento-vehiculos-production.up.railway.app"
    
    # Datos del vehículo AB 844
    vehicle_data = {
        "placa": "AB 844",
        "marca": "TOYOTA", 
        "modelo": "CAMION HINO",
        "ano": 2025,
        "color": "BLANCO",
        "propietario": "Holding",
        "poliza": "POL4515",
        "seguro": "QUALITAS",
        "km_inicial": 25552
    }
    
    print("🚗 AGREGANDO VEHÍCULO AB 844")
    print(f"📝 Datos: {vehicle_data}")
    
    # 1. Verificar estado inicial
    print("\n📊 1. ESTADO INICIAL:")
    try:
        response = requests.get(f"{api_url}/vehiculos", timeout=10)
        if response.status_code == 200:
            initial_data = response.json()
            if initial_data.get("success"):
                initial_count = len(initial_data.get("data", []))
                print(f"   Vehículos actuales: {initial_count}")
                for v in initial_data.get("data", []):
                    print(f"   - {v.get('placa')} - {v.get('marca')} {v.get('modelo')}")
            else:
                print("   ❌ Error obteniendo estado inicial")
                return False
        else:
            print(f"   ❌ HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # 2. Agregar el vehículo
    print(f"\n💾 2. AGREGANDO VEHÍCULO:")
    try:
        response = requests.post(
            f"{api_url}/vehiculos",
            json=vehicle_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   HTTP Status: {response.status_code}")
        print(f"   Respuesta: {response.text}")
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            
            if response_data.get("success"):
                print(f"   ✅ {response_data.get('message', 'Vehículo creado')}")
                
                if 'vehiculo_id' in response_data:
                    print(f"   🆔 ID asignado: {response_data['vehiculo_id']}")
                
                if 'total_vehiculos' in response_data:
                    print(f"   📊 Total vehículos: {response_data['total_vehiculos']}")
                
            else:
                print(f"   ❌ Error en respuesta: {response_data}")
                return False
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Detalles: {error_data}")
            except:
                print(f"   Respuesta cruda: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error en request: {e}")
        return False
    
    # 3. Esperar y verificar
    print(f"\n⏳ 3. ESPERANDO SINCRONIZACIÓN...")
    time.sleep(3)
    
    # 4. Verificar estado final
    print(f"\n✅ 4. VERIFICACIÓN FINAL:")
    try:
        response = requests.get(f"{api_url}/vehiculos", timeout=10)
        if response.status_code == 200:
            final_data = response.json()
            if final_data.get("success"):
                final_count = len(final_data.get("data", []))
                print(f"   Vehículos finales: {final_count}")
                
                # Buscar específicamente AB 844
                ab844_found = False
                for v in final_data.get("data", []):
                    placa = v.get('placa', '')
                    if 'AB 844' in placa or 'AB844' in placa.replace(' ', ''):
                        ab844_found = True
                        print(f"   🎯 AB 844 ENCONTRADO:")
                        print(f"      ID: {v.get('id')}")
                        print(f"      Placa: {v.get('placa')}")
                        print(f"      Marca: {v.get('marca')}")
                        print(f"      Modelo: {v.get('modelo')}")
                        print(f"      Año: {v.get('ano')}")
                        print(f"      KM: {v.get('km_inicial')}")
                        print(f"      Creado: {v.get('created_at')}")
                
                if not ab844_found:
                    print(f"   ❌ AB 844 NO ENCONTRADO")
                    print(f"   📋 Vehículos actuales:")
                    for v in final_data.get("data", []):
                        print(f"      - {v.get('placa')} - {v.get('marca')} {v.get('modelo')}")
                    return False
                
                # Verificar incremento
                if final_count > initial_count:
                    print(f"   ✅ INCREMENTO CONFIRMADO: +{final_count - initial_count}")
                    return True
                else:
                    print(f"   ❌ SIN INCREMENTO: {initial_count} → {final_count}")
                    return False
                    
            else:
                print("   ❌ Error obteniendo estado final")
                return False
        else:
            print(f"   ❌ HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_sync_status():
    """Verificar estado de sincronización"""
    api_url = "https://mantenimiento-vehiculos-production.up.railway.app"
    
    try:
        response = requests.get(f"{api_url}/force-sync-check", timeout=10)
        if response.status_code == 200:
            sync_data = response.json()
            if sync_data.get("success"):
                report = sync_data.get("sync_report", {})
                print(f"\n🔄 ESTADO DE SINCRONIZACIÓN:")
                print(f"   Status: {report.get('sync_status')}")
                print(f"   Total registros: {report.get('total_records')}")
                
                tables = report.get("tables_info", {})
                if 'vehiculos' in tables:
                    vehiculos_info = tables['vehiculos']
                    print(f"   Vehículos: {vehiculos_info.get('count')} registros")
                    
                return True
            else:
                print(f"\n❌ Error en sync-check: {sync_data}")
                return False
        else:
            print(f"\n❌ Sync-check HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"\n❌ Error verificando sync: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBA DE AGREGADO DE VEHÍCULO AB 844\n")
    
    # Verificar sincronización inicial
    check_sync_status()
    
    # Agregar vehículo
    success = add_vehicle_ab844()
    
    if success:
        print(f"\n🎉 ¡ÉXITO! Vehículo AB 844 agregado y verificado")
        
        # Verificar sincronización final
        check_sync_status()
    else:
        print(f"\n❌ FALLÓ: El vehículo no se agregó correctamente")
    
    print(f"\n📅 Prueba completada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")