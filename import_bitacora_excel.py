#!/usr/bin/env python3
"""
Importar registros de bitácora desde archivo Excel
Procesa el archivo bitacora_nueva_2025-09-02.xlsx y agrega los registros de bitácora al sistema
"""

import pandas as pd
import sqlite3
import sys
import logging
from datetime import datetime, timezone, timedelta
import os
import numpy as np

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurar zona horaria de Centroamérica (GMT-6)
CENTRAL_AMERICA_TZ = timezone(timedelta(hours=-6))

def now_ca():
    """Obtener la fecha/hora actual en zona horaria de Centroamérica (GMT-6)"""
    return datetime.now(CENTRAL_AMERICA_TZ)

def get_db_connection():
    """Obtener conexión a la base de datos"""
    db_path = "vehicular_system.db"
    if not os.path.exists(db_path):
        logger.error(f"❌ Base de datos no encontrada: {db_path}")
        return None
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def leer_excel_bitacora(archivo_excel):
    """Leer datos de bitácora del archivo Excel"""
    try:
        logger.info(f"📖 Leyendo archivo Excel: {archivo_excel}")
        
        # Leer la hoja de Bitácora
        df = pd.read_excel(archivo_excel, sheet_name='Bitácora')
        
        logger.info(f"📊 Columnas encontradas: {list(df.columns)}")
        logger.info(f"📈 Filas encontradas: {len(df)}")
        
        return df
        
    except Exception as e:
        logger.error(f"❌ Error leyendo archivo Excel: {e}")
        return None

def parsear_fecha(fecha_str):
    """Parsear fecha desde diferentes formatos"""
    if pd.isna(fecha_str) or fecha_str == '' or fecha_str is None:
        return None
    
    try:
        # Formato: '1/9/2025, 9:57:17 p. m.'
        fecha_str = str(fecha_str).replace('p.\xa0m.', 'PM').replace('a.\xa0m.', 'AM')
        fecha_str = fecha_str.replace('p. m.', 'PM').replace('a. m.', 'AM')
        
        # Probar diferentes formatos
        formatos = [
            '%d/%m/%Y, %I:%M:%S %p',
            '%d/%m/%Y %I:%M:%S %p',
            '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d'
        ]
        
        for formato in formatos:
            try:
                fecha = datetime.strptime(fecha_str, formato)
                # Convertir a zona horaria de Centroamérica
                fecha = fecha.replace(tzinfo=CENTRAL_AMERICA_TZ)
                return fecha
            except ValueError:
                continue
        
        logger.warning(f"⚠️ No se pudo parsear fecha: {fecha_str}")
        return None
        
    except Exception as e:
        logger.warning(f"⚠️ Error parseando fecha {fecha_str}: {e}")
        return None

def validar_vehiculo_existe(conn, placa):
    """Verificar si el vehículo existe en la base de datos"""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM vehiculos WHERE placa = ?", (placa,))
    result = cursor.fetchone()
    return result is not None

def verificar_bitacora_existente(conn, placa, fecha_salida):
    """Verificar si ya existe un registro de bitácora para esta placa y fecha"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM bitacora 
        WHERE placa = ? AND DATE(fecha_salida) = DATE(?)
    """, (placa, fecha_salida.isoformat()))
    result = cursor.fetchone()
    return result is not None

def insertar_registro_bitacora(conn, registro):
    """Insertar un registro de bitácora en la base de datos"""
    try:
        cursor = conn.cursor()
        
        # Extraer y validar datos
        placa = registro.get('Placa', '').strip().upper()
        chofer = registro.get('Chofer', '').strip()
        fecha_salida_str = registro.get('Fecha Salida')
        km_salida = registro.get('Km Salida', 0)
        combustible_salida = registro.get('Combustible Salida', '1/2')
        estado_salida = registro.get('Estado Salida', 'bueno')
        fecha_retorno_str = registro.get('Fecha Retorno')
        km_retorno = registro.get('Km Retorno')
        combustible_retorno = registro.get('Combustible Retorno')
        estado_retorno = registro.get('Estado Retorno')
        observaciones = registro.get('Observaciones', '')
        estado = registro.get('Estado', 'en_curso')
        
        # Validaciones básicas
        if not placa or not chofer:
            logger.warning("⚠️ Registro omitido - placa o chofer vacío")
            return False
        
        # Verificar si el vehículo existe
        if not validar_vehiculo_existe(conn, placa):
            logger.warning(f"⚠️ Vehículo {placa} no existe en la base de datos")
            return False
        
        # Parsear fechas
        fecha_salida = parsear_fecha(fecha_salida_str)
        if not fecha_salida:
            logger.warning(f"⚠️ Fecha de salida inválida para {placa}: {fecha_salida_str}")
            return False
        
        # Verificar si ya existe el registro
        if verificar_bitacora_existente(conn, placa, fecha_salida):
            logger.warning(f"⚠️ Ya existe registro de bitácora para {placa} en {fecha_salida.date()}")
            return False
        
        fecha_retorno = parsear_fecha(fecha_retorno_str) if fecha_retorno_str and not pd.isna(fecha_retorno_str) else None
        
        # Limpiar observaciones
        if pd.isna(observaciones) or observaciones == 'nan':
            observaciones = ''
        
        # Limpiar valores NaN
        if pd.isna(km_retorno):
            km_retorno = None
        else:
            km_retorno = int(float(km_retorno))
            
        if pd.isna(combustible_retorno):
            combustible_retorno = None
            
        if pd.isna(estado_retorno):
            estado_retorno = None
        
        # Insertar registro
        cursor.execute("""
            INSERT INTO bitacora (
                placa, chofer, fecha_salida, km_salida, nivel_combustible_salida, 
                estado_vehiculo_salida, fecha_retorno, km_retorno, nivel_combustible_retorno,
                estado_vehiculo_retorno, observaciones, estado, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            placa,
            chofer,
            fecha_salida.isoformat(),
            int(km_salida),
            combustible_salida,
            estado_salida,
            fecha_retorno.isoformat() if fecha_retorno else None,
            km_retorno,
            combustible_retorno,
            estado_retorno,
            observaciones,
            estado,
            now_ca().isoformat()
        ))
        
        logger.info(f"✅ Registro insertado: {placa} - {chofer} - {fecha_salida.strftime('%d/%m/%Y %H:%M')} - Estado: {estado}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error insertando registro para {registro.get('Placa', 'N/A')}: {e}")
        return False

def main():
    """Función principal"""
    archivo_excel = "bitacora_nueva_2025-09-02.xlsx"
    
    logger.info("🚀 === INICIANDO IMPORTACIÓN DE BITÁCORA ===")
    
    # Verificar que el archivo exista
    if not os.path.exists(archivo_excel):
        logger.error(f"❌ Archivo no encontrado: {archivo_excel}")
        return
    
    # Leer archivo Excel
    df = leer_excel_bitacora(archivo_excel)
    if df is None or df.empty:
        logger.error("❌ No se pudo leer el archivo Excel o está vacío")
        return
    
    logger.info(f"📊 Procesando {len(df)} registros de bitácora")
    
    # Conectar a la base de datos
    conn = get_db_connection()
    if not conn:
        logger.error("❌ No se pudo conectar a la base de datos")
        return
    
    # Insertar registros
    exitosos = 0
    fallidos = 0
    duplicados = 0
    
    logger.info(f"💾 Procesando {len(df)} registros...")
    
    for i, (index, registro) in enumerate(df.iterrows()):
        logger.info(f"🔄 Procesando registro {i+1}/{len(df)}: {registro.get('Placa', 'N/A')} - {registro.get('Chofer', 'N/A')}")
        
        if insertar_registro_bitacora(conn, registro):
            exitosos += 1
        else:
            fallidos += 1
    
    # Guardar cambios
    conn.commit()
    conn.close()
    
    # Resumen final
    logger.info("🎯 === RESUMEN DE IMPORTACIÓN ===")
    logger.info(f"✅ Registros exitosos: {exitosos}")
    logger.info(f"❌ Registros fallidos: {fallidos}")
    logger.info(f"📊 Total procesados: {exitosos + fallidos}")
    
    if exitosos > 0:
        logger.info("🎉 ¡Importación de bitácora completada exitosamente!")
        logger.info("💡 Los registros han sido agregados a la bitácora del sistema")
    else:
        logger.warning("⚠️ No se importaron registros de bitácora")

if __name__ == "__main__":
    main()