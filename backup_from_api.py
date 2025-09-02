#!/usr/bin/env python3
"""
Backup de datos directamente desde la API de Railway
Para capturar el estado real de producción
"""

import requests
import json
import zipfile
import csv
from datetime import datetime
import os

def backup_from_railway_api():
    """Crear backup completo desde la API de Railway"""
    
    api_base = "https://mantenimiento-vehiculos-production.up.railway.app"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"railway_api_backup_{timestamp}"
    
    # Crear directorio temporal
    backup_dir = f"/home/user/webapp/api_backups/{backup_name}"
    os.makedirs(backup_dir, exist_ok=True)
    
    endpoints = [
        "vehiculos",
        "mantenimientos", 
        "combustible",
        "revisiones",
        "polizas",
        "rtv",
        "bitacora"
    ]
    
    backup_data = {
        "backup_info": {
            "timestamp": datetime.now().isoformat(),
            "source": "Railway API",
            "api_base": api_base,
            "backup_name": backup_name
        },
        "data": {}
    }
    
    stats = {}
    
    try:
        for endpoint in endpoints:
            print(f"📡 Obteniendo datos de {endpoint}...")
            
            try:
                response = requests.get(f"{api_base}/{endpoint}", timeout=30)
                
                if response.status_code == 200:
                    api_response = response.json()
                    
                    if api_response.get("success") and "data" in api_response:
                        data = api_response["data"]
                        backup_data["data"][endpoint] = data
                        stats[endpoint] = len(data)
                        
                        # Crear CSV para cada endpoint
                        if data:
                            csv_path = f"{backup_dir}/{endpoint}.csv"
                            
                            # Obtener nombres de columnas del primer registro
                            if isinstance(data[0], dict):
                                fieldnames = data[0].keys()
                                
                                with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                    writer.writeheader()
                                    writer.writerows(data)
                                
                                print(f"  ✅ {len(data)} registros guardados en CSV")
                            else:
                                print(f"  ⚠️ Formato inesperado en {endpoint}")
                        else:
                            stats[endpoint] = 0
                            print(f"  📝 Sin registros en {endpoint}")
                    else:
                        stats[endpoint] = 0
                        print(f"  ❌ Error en respuesta de {endpoint}")
                else:
                    stats[endpoint] = 0
                    print(f"  ❌ HTTP {response.status_code} para {endpoint}")
                    
            except Exception as e:
                stats[endpoint] = 0
                print(f"  ❌ Error obteniendo {endpoint}: {e}")
        
        # Guardar backup completo en JSON
        json_path = f"{backup_dir}/complete_backup.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)
        
        # Guardar estadísticas
        backup_data["backup_info"]["stats"] = stats
        backup_data["backup_info"]["total_records"] = sum(stats.values())
        
        stats_path = f"{backup_dir}/backup_stats.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data["backup_info"], f, indent=2, ensure_ascii=False)
        
        # Crear ZIP del backup
        zip_path = f"/home/user/webapp/api_backups/{backup_name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, backup_dir)
                    zipf.write(file_path, arcname)
        
        # Mostrar resumen
        print(f"\n📊 RESUMEN DEL BACKUP:")
        print(f"🕐 Timestamp: {backup_data['backup_info']['timestamp']}")
        print(f"📁 Archivo: {zip_path}")
        print(f"📋 Estadísticas:")
        
        total_records = 0
        for endpoint, count in stats.items():
            print(f"   🚗 {endpoint.capitalize()}: {count} registros")
            total_records += count
        
        print(f"📊 Total de registros: {total_records}")
        
        # Mostrar detalles de vehículos si los hay
        if "vehiculos" in backup_data["data"] and backup_data["data"]["vehiculos"]:
            print(f"\n🚗 VEHÍCULOS ENCONTRADOS:")
            for i, vehiculo in enumerate(backup_data["data"]["vehiculos"], 1):
                print(f"   {i}) {vehiculo['placa']} - {vehiculo['marca']} {vehiculo['modelo']} ({vehiculo['ano']})")
        
        return True, zip_path, backup_data["backup_info"]
        
    except Exception as e:
        print(f"❌ Error general en backup: {e}")
        return False, None, None

if __name__ == "__main__":
    print("🔄 Iniciando backup desde Railway API...")
    
    # Crear directorio de backups de API
    os.makedirs("/home/user/webapp/api_backups", exist_ok=True)
    
    success, backup_file, backup_info = backup_from_railway_api()
    
    if success:
        print(f"\n✅ BACKUP COMPLETADO EXITOSAMENTE")
        print(f"📁 Archivo: {backup_file}")
        print(f"📊 {backup_info['total_records']} registros respaldados")
    else:
        print(f"\n❌ BACKUP FALLÓ")