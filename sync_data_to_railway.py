#!/usr/bin/env python3
"""
Sincronizar datos locales con Railway
Envía los registros de la base de datos local a la API de Railway
"""

import sqlite3
import requests
import json
import logging
from datetime import datetime
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URLs de las APIs
RAILWAY_API = "https://mantenimiento-vehiculos-production.up.railway.app"
LOCAL_DB = "vehicular_system.db"

def get_local_data():
    """Obtener datos de la base de datos local"""
    if not os.path.exists(LOCAL_DB):
        logger.error(f"❌ Base de datos local no encontrada: {LOCAL_DB}")
        return None, None
    
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Obtener registros de combustible
        cursor.execute("SELECT * FROM combustible ORDER BY fecha DESC")
        combustible_local = [dict(row) for row in cursor.fetchall()]
        
        # Obtener registros de bitácora  
        cursor.execute("SELECT * FROM bitacora ORDER BY fecha_salida DESC")
        bitacora_local = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        logger.info(f"📊 Datos locales: {len(combustible_local)} combustible, {len(bitacora_local)} bitácora")
        return combustible_local, bitacora_local
        
    except Exception as e:
        logger.error(f"❌ Error leyendo datos locales: {e}")
        conn.close()
        return None, None

def get_railway_data():
    """Obtener datos existentes en Railway"""
    try:
        # Obtener combustible de Railway
        response = requests.get(f"{RAILWAY_API}/combustible", timeout=10)
        combustible_railway = response.json()['data'] if response.ok else []
        
        # Obtener bitácora de Railway
        response = requests.get(f"{RAILWAY_API}/bitacora", timeout=10)
        bitacora_railway = response.json()['data'] if response.ok else []
        
        logger.info(f"🌐 Datos Railway: {len(combustible_railway)} combustible, {len(bitacora_railway)} bitácora")
        return combustible_railway, bitacora_railway
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos de Railway: {e}")
        return [], []

def enviar_combustible_a_railway(registro):
    """Enviar un registro de combustible a Railway"""
    try:
        # Preparar datos para Railway
        data = {
            "placa": registro['placa'],
            "fecha": registro['fecha'],
            "litros": float(registro['litros']),
            "costo": float(registro['costo']),
            "kilometraje": int(registro['kilometraje']) if registro['kilometraje'] else 0,
            "estacion": registro['estacion'] or "Importado desde local"
        }
        
        logger.info(f"📤 Enviando combustible: {data['placa']} - {data['fecha']} - {data['litros']}L")
        
        response = requests.post(
            f"{RAILWAY_API}/combustible",
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.ok:
            result = response.json()
            logger.info(f"✅ Combustible enviado exitosamente: ID {result.get('id', 'N/A')}")
            return True
        else:
            logger.error(f"❌ Error enviando combustible: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en envío de combustible: {e}")
        return False

def enviar_bitacora_a_railway(registro):
    """Enviar un registro de bitácora a Railway"""
    try:
        # Determinar si es salida o retorno completo
        if registro['estado'] == 'completado' and registro['fecha_retorno']:
            # Enviar salida y retorno
            return enviar_salida_y_retorno(registro)
        else:
            # Enviar solo salida
            return enviar_solo_salida(registro)
            
    except Exception as e:
        logger.error(f"❌ Error en envío de bitácora: {e}")
        return False

def enviar_solo_salida(registro):
    """Enviar solo registro de salida"""
    try:
        data = {
            "placa": registro['placa'],
            "chofer": registro['chofer'],
            "km_salida": int(registro['km_salida']),
            "nivel_combustible_salida": registro['nivel_combustible_salida'],
            "estado_vehiculo_salida": registro['estado_vehiculo_salida'],
            "observaciones": registro['observaciones'] or ""
        }
        
        logger.info(f"📤 Enviando salida: {data['placa']} - {data['chofer']}")
        
        response = requests.post(
            f"{RAILWAY_API}/bitacora/salida",
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.ok:
            result = response.json()
            bitacora_id = result.get('bitacora_id')
            logger.info(f"✅ Salida enviada exitosamente: ID {bitacora_id}")
            return bitacora_id
        else:
            logger.error(f"❌ Error enviando salida: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en envío de salida: {e}")
        return False

def enviar_retorno(bitacora_id, registro):
    """Enviar registro de retorno"""
    try:
        data = {
            "km_retorno": int(registro['km_retorno']),
            "nivel_combustible_retorno": registro['nivel_combustible_retorno'],
            "estado_vehiculo_retorno": registro['estado_vehiculo_retorno'],
            "observaciones": registro['observaciones'] or ""
        }
        
        logger.info(f"📤 Enviando retorno para bitácora ID {bitacora_id}")
        
        response = requests.put(
            f"{RAILWAY_API}/bitacora/{bitacora_id}/retorno",
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.ok:
            result = response.json()
            logger.info(f"✅ Retorno enviado exitosamente")
            return True
        else:
            logger.error(f"❌ Error enviando retorno: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en envío de retorno: {e}")
        return False

def enviar_salida_y_retorno(registro):
    """Enviar salida y luego retorno"""
    # Primero enviar la salida
    bitacora_id = enviar_solo_salida(registro)
    
    if bitacora_id:
        # Luego enviar el retorno
        return enviar_retorno(bitacora_id, registro)
    else:
        return False

def sincronizar_datos():
    """Función principal de sincronización"""
    logger.info("🚀 === INICIANDO SINCRONIZACIÓN LOCAL → RAILWAY ===")
    
    # Obtener datos
    combustible_local, bitacora_local = get_local_data()
    if not combustible_local and not bitacora_local:
        logger.error("❌ No hay datos locales para sincronizar")
        return
    
    combustible_railway, bitacora_railway = get_railway_data()
    
    # Sincronizar combustible
    logger.info("⛽ === SINCRONIZANDO COMBUSTIBLE ===")
    combustible_exitosos = 0
    
    for registro in combustible_local:
        # Verificar si ya existe en Railway (por placa y fecha)
        existe = any(
            r['placa'] == registro['placa'] and r['fecha'] == registro['fecha'] 
            for r in combustible_railway
        )
        
        if not existe:
            if enviar_combustible_a_railway(registro):
                combustible_exitosos += 1
        else:
            logger.info(f"⏭️ Combustible ya existe: {registro['placa']} - {registro['fecha']}")
    
    # Sincronizar bitácora
    logger.info("📝 === SINCRONIZANDO BITÁCORA ===")
    bitacora_exitosos = 0
    
    for registro in bitacora_local:
        # Verificar si ya existe en Railway (por placa y fecha de salida)
        existe = any(
            r['placa'] == registro['placa'] and 
            r['fecha_salida'][:10] == registro['fecha_salida'][:10]  # Comparar solo fecha, no hora
            for r in bitacora_railway
        )
        
        if not existe:
            if enviar_bitacora_a_railway(registro):
                bitacora_exitosos += 1
        else:
            logger.info(f"⏭️ Bitácora ya existe: {registro['placa']} - {registro['fecha_salida'][:10]}")
    
    # Resumen final
    logger.info("🎯 === RESUMEN DE SINCRONIZACIÓN ===")
    logger.info(f"✅ Combustible sincronizado: {combustible_exitosos}/{len(combustible_local)}")
    logger.info(f"✅ Bitácora sincronizada: {bitacora_exitosos}/{len(bitacora_local)}")
    
    if combustible_exitosos > 0 or bitacora_exitosos > 0:
        logger.info("🎉 ¡Sincronización completada! Los datos deberían aparecer en Railway ahora.")
    else:
        logger.info("ℹ️ Todos los datos ya estaban sincronizados.")

if __name__ == "__main__":
    sincronizar_datos()