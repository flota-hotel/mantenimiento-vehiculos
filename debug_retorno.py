#!/usr/bin/env python3
"""
Script de debug para el problema del botón de retorno
"""

import sqlite3
import json
import requests
from datetime import datetime

def debug_bitacora_state():
    """Debug del estado actual de la bitácora"""
    print("🔍 DEBUGEANDO ESTADO DE BITÁCORA")
    print("=" * 50)
    
    # 1. Verificar base de datos local
    conn = sqlite3.connect("vehicular_system.db")
    cursor = conn.cursor()
    
    # Obtener registros de bitácora
    cursor.execute("SELECT * FROM bitacora ORDER BY id")
    registros = cursor.fetchall()
    
    print(f"📝 REGISTROS EN BASE DE DATOS: {len(registros)}")
    for registro in registros:
        print(f"   ID: {registro[0]} - Placa: {registro[1]} - Chofer: {registro[2]} - Estado: {registro[12]}")
        if registro[12] == 'en_curso':  # estado
            print(f"      🔄 EN CURSO: Salida={registro[3][:19]}, Km={registro[4]}")
    
    conn.close()
    print()
    
    # 2. Verificar API de Railway
    try:
        API_URL = "https://mantenimiento-vehiculos-production.up.railway.app"
        
        print(f"🌐 VERIFICANDO API DE RAILWAY: {API_URL}")
        
        # Obtener bitácora desde API
        response = requests.get(f"{API_URL}/bitacora", timeout=10)
        if response.status_code == 200:
            data = response.json()
            registros_api = data.get('data', [])
            print(f"📊 REGISTROS EN RAILWAY API: {len(registros_api)}")
            
            for registro in registros_api:
                print(f"   ID: {registro['id']} - Placa: {registro['placa']} - Chofer: {registro['chofer']} - Estado: {registro['estado']}")
                if registro['estado'] == 'en_curso':
                    print(f"      🔄 EN CURSO: Salida={registro['fecha_salida'][:19]}, Km={registro['km_salida']}")
        else:
            print(f"❌ Error en API: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error conectando a Railway: {e}")
    
    print()

def test_retorno_endpoint():
    """Probar el endpoint de retorno directamente"""
    print("🧪 PROBANDO ENDPOINT DE RETORNO")
    print("=" * 50)
    
    API_URL = "https://mantenimiento-vehiculos-production.up.railway.app"
    
    # Obtener un registro en curso
    try:
        response = requests.get(f"{API_URL}/bitacora", timeout=10)
        if response.status_code == 200:
            data = response.json()
            registros = data.get('data', [])
            
            # Buscar registro en curso
            registro_en_curso = None
            for registro in registros:
                if registro['estado'] == 'en_curso':
                    registro_en_curso = registro
                    break
            
            if not registro_en_curso:
                print("❌ No hay registros en curso para probar")
                return
            
            print(f"🎯 PROBANDO RETORNO PARA:")
            print(f"   ID: {registro_en_curso['id']}")
            print(f"   Placa: {registro_en_curso['placa']}")
            print(f"   Chofer: {registro_en_curso['chofer']}")
            
            # Datos de retorno de prueba
            retorno_data = {
                "km_retorno": int(registro_en_curso['km_salida']) + 50,  # +50 km
                "nivel_combustible_retorno": "1/2",
                "estado_vehiculo_retorno": "bueno",
                "observaciones": "Test de retorno desde debug"
            }
            
            print(f"📤 ENVIANDO DATOS DE RETORNO:")
            print(json.dumps(retorno_data, indent=2))
            
            # Hacer la petición PUT
            response = requests.put(
                f"{API_URL}/bitacora/{registro_en_curso['id']}/retorno",
                json=retorno_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"📥 RESPUESTA DEL SERVIDOR:")
            print(f"   Status Code: {response.status_code}")
            print(f"   Content: {response.text}")
            
            if response.status_code == 200:
                print("✅ ENDPOINT DE RETORNO FUNCIONA CORRECTAMENTE")
            else:
                print("❌ ERROR EN ENDPOINT DE RETORNO")
                
        else:
            print(f"❌ Error obteniendo bitácora: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error en prueba de endpoint: {e}")

if __name__ == "__main__":
    debug_bitacora_state()
    print()
    test_retorno_endpoint()