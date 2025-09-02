#!/usr/bin/env python3
"""
Debug script to verify dashboard data and renderKpis issues
"""
import requests
import json
from datetime import datetime

# API endpoints
API_URL = "https://mantenimiento-vehiculos-production.up.railway.app"

def verify_production_data():
    """Verificar datos en producción"""
    print("🔍 === VERIFICANDO DATOS EN PRODUCCIÓN ===\n")
    
    endpoints = [
        ("combustible", "⛽ Combustible"),
        ("mantenimientos", "🔧 Mantenimientos"), 
        ("polizas", "🛡️ Pólizas"),
        ("bitacora", "📝 Bitácora"),
        ("vehiculos", "🚗 Vehículos")
    ]
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{API_URL}/{endpoint}", timeout=10)
            if response.ok:
                data = response.json()
                if data.get("success"):
                    records = data.get("data", [])
                    print(f"✅ {name}: {len(records)} registros")
                    if records and len(records) > 0:
                        print(f"   📋 Primer registro: {records[0]}")
                    print()
                else:
                    print(f"❌ {name}: API error - {data}")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
        print()

def calculate_expected_kpis():
    """Calcular KPIs esperados manualmente"""
    print("🧮 === CALCULANDO KPIs ESPERADOS ===\n")
    
    try:
        # Obtener datos de combustible
        response = requests.get(f"{API_URL}/combustible", timeout=10)
        combustible_data = response.json()
        
        if combustible_data.get("success"):
            records = combustible_data.get("data", [])
            print(f"🔥 COMBUSTIBLE ANALYSIS:")
            print(f"   Total registros: {len(records)}")
            
            if records:
                # Calcular costos del mes actual
                now = datetime.now()
                inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                print(f"   Inicio del mes: {inicio_mes}")
                
                total_mes = 0
                registros_mes = 0
                
                for record in records:
                    fecha_str = record.get("fecha", "")
                    costo = float(record.get("costo", 0))
                    
                    try:
                        # Parsear fecha (varios formatos posibles)
                        if "T" in fecha_str:
                            fecha = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                        else:
                            fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                        
                        print(f"   📊 {record.get('placa', 'N/A')}: {fecha_str} -> ₡{costo:,.2f}")
                        
                        # Verificar si está en el mes actual
                        if fecha >= inicio_mes:
                            total_mes += costo
                            registros_mes += 1
                            print(f"      ✅ Incluido en mes actual")
                        else:
                            print(f"      ❌ Fuera del mes actual")
                    except Exception as e:
                        print(f"      ⚠️ Error parseando fecha: {e}")
                
                print(f"\n   💰 TOTAL MES ACTUAL: ₡{total_mes:,.2f}")
                print(f"   📊 REGISTROS MES: {registros_mes}")
                
                # Verificar formato de fecha esperado por frontend
                print(f"\n   🔍 FORMATO FECHA ANÁLISIS:")
                for record in records:
                    fecha_str = record.get("fecha", "")
                    print(f"      {record.get('placa')}: '{fecha_str}' -> new Date('{fecha_str}')")
                
        else:
            print("❌ Error obteniendo datos de combustible")
            
    except Exception as e:
        print(f"❌ Error calculando KPIs: {e}")

def verify_frontend_compatibility():
    """Verificar compatibilidad con frontend"""
    print("\n🔧 === VERIFICANDO COMPATIBILIDAD FRONTEND ===\n")
    
    try:
        response = requests.get(f"{API_URL}/combustible", timeout=10)
        data = response.json()
        
        if data.get("success"):
            records = data.get("data", [])
            print("📋 Estructura de datos de combustible:")
            if records:
                record = records[0]
                print(f"   Campos disponibles: {list(record.keys())}")
                print(f"   Fecha formato: '{record.get('fecha')}' (tipo: {type(record.get('fecha'))})")
                print(f"   Costo formato: {record.get('costo')} (tipo: {type(record.get('costo'))})")
                print(f"   Placa: '{record.get('placa')}'")
                
                # Simular lo que hace el frontend
                fecha_js = record.get('fecha')
                print(f"\n🔍 Simulación JavaScript:")
                print(f"   new Date('{fecha_js}') sería válido: {fecha_js is not None}")
                print(f"   Number('{record.get('costo')}') = {float(record.get('costo', 0))}")
    
    except Exception as e:
        print(f"❌ Error verificando compatibilidad: {e}")

if __name__ == "__main__":
    verify_production_data()
    calculate_expected_kpis()
    verify_frontend_compatibility()
    
    print("\n🎯 === DIAGNÓSTICO COMPLETO ===")
    print("Si hay registros de combustible pero los KPIs muestran ₡0:")
    print("1. ✅ Verificar que renderKpis() se ejecute después de loadAll()")
    print("2. ✅ Verificar que los arrays Combustible/Mantenimientos no estén vacíos")  
    print("3. ✅ Verificar formato de fechas en filtros del mes actual")
    print("4. ✅ Verificar que los elementos DOM existan (byId)")
    print("5. ✅ Verificar función fmt() para formateo de números")