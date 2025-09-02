#!/usr/bin/env python3
"""
Importar registros de combustible desde archivo Excel
Procesa el archivo bitacora_nueva_2025-09-02.xlsx y agrega los registros al sistema
"""

import pandas as pd
import sqlite3
import sys
import logging
from datetime import datetime, timezone, timedelta
import os

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

def leer_excel_combustible(archivo_excel):
    """Leer datos de combustible del archivo Excel"""
    try:
        logger.info(f"📖 Leyendo archivo Excel: {archivo_excel}")
        
        # Leer todas las hojas del Excel para encontrar los datos
        excel_file = pd.ExcelFile(archivo_excel)
        logger.info(f"📋 Hojas disponibles: {excel_file.sheet_names}")
        
        # Probar diferentes hojas
        for sheet_name in excel_file.sheet_names:
            try:
                logger.info(f"🔍 Procesando hoja: {sheet_name}")
                df = pd.read_excel(archivo_excel, sheet_name=sheet_name)
                
                logger.info(f"📊 Columnas encontradas: {list(df.columns)}")
                logger.info(f"📈 Filas encontradas: {len(df)}")
                
                # Mostrar las primeras filas para debugging
                if not df.empty:
                    logger.info("🔍 Primeras 3 filas:")
                    for i, row in df.head(3).iterrows():
                        logger.info(f"   Fila {i}: {dict(row)}")
                
                return df, sheet_name
                
            except Exception as e:
                logger.warning(f"⚠️ Error leyendo hoja {sheet_name}: {e}")
                continue
        
        logger.error("❌ No se pudo leer ninguna hoja del archivo Excel")
        return None, None
        
    except Exception as e:
        logger.error(f"❌ Error leyendo archivo Excel: {e}")
        return None, None

def mapear_columnas(df):
    """Mapear las columnas del Excel a los campos de la base de datos"""
    # Mapeo de posibles nombres de columnas
    column_mapping = {
        # Columnas esperadas en español
        'PLACA': 'placa',
        'placa': 'placa', 
        'Placa': 'placa',
        'FECHA': 'fecha',
        'fecha': 'fecha',
        'Fecha': 'fecha',
        'LITROS': 'litros',
        'litros': 'litros',
        'Litros': 'litros',
        '₡/L': 'precio_por_litro',
        'PRECIO': 'precio_por_litro',
        'precio': 'precio_por_litro',
        'Precio/Litro': 'precio_por_litro',
        'COSTO': 'costo',
        'costo': 'costo',
        'Costo': 'costo',
        'ODÓMETRO': 'odometro_actual',
        'ODOMETRO': 'odometro_actual', 
        'odometro': 'odometro_actual',
        'Odómetro': 'odometro_actual',
        'KM/L': 'km_por_litro',
        'km/l': 'km_por_litro',
        'Km/L': 'km_por_litro'
    }
    
    logger.info("🗺️ Mapeando columnas...")
    
    # Crear DataFrame con columnas mapeadas
    mapped_data = []
    
    for index, row in df.iterrows():
        registro = {}
        
        # Mapear cada columna
        for col in df.columns:
            if col in column_mapping:
                db_field = column_mapping[col]
                registro[db_field] = row[col]
        
        # Validar que tenga los campos mínimos requeridos
        if 'placa' in registro and 'fecha' in registro and 'litros' in registro:
            mapped_data.append(registro)
        else:
            logger.warning(f"⚠️ Fila {index} omitida - faltan campos requeridos: {registro}")
    
    logger.info(f"✅ {len(mapped_data)} registros válidos mapeados")
    return mapped_data

def validar_vehiculo_existe(conn, placa):
    """Verificar si el vehículo existe en la base de datos"""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM vehiculos WHERE placa = ?", (placa,))
    result = cursor.fetchone()
    return result is not None

def insertar_registro_combustible(conn, registro):
    """Insertar un registro de combustible en la base de datos"""
    try:
        cursor = conn.cursor()
        
        # Preparar datos con valores por defecto si faltan
        placa = registro.get('placa', '').strip().upper()
        fecha = registro.get('fecha', now_ca().date())
        litros = float(registro.get('litros', 0))
        precio_por_litro = float(registro.get('precio_por_litro', 0))
        costo = float(registro.get('costo', litros * precio_por_litro))
        odometro_actual = int(registro.get('odometro_actual', 0))
        km_por_litro = float(registro.get('km_por_litro', 0)) if registro.get('km_por_litro') else None
        
        # Validaciones básicas
        if not placa:
            logger.warning("⚠️ Registro omitido - placa vacía")
            return False
            
        if litros <= 0:
            logger.warning(f"⚠️ Registro omitido para {placa} - litros inválidos: {litros}")
            return False
        
        # Verificar si el vehículo existe
        if not validar_vehiculo_existe(conn, placa):
            logger.warning(f"⚠️ Vehículo {placa} no existe en la base de datos")
            return False
        
        # Convertir fecha si es necesario
        if isinstance(fecha, str):
            try:
                fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
            except ValueError:
                try:
                    fecha = datetime.strptime(fecha, '%d/%m/%Y').date()
                except ValueError:
                    logger.warning(f"⚠️ Fecha inválida para {placa}: {fecha}")
                    fecha = now_ca().date()
        
        # Insertar registro
        cursor.execute("""
            INSERT INTO combustible (
                placa, fecha, litros, precio_por_litro, costo, 
                odometro_actual, km_por_litro, proveedor, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            placa,
            fecha.strftime('%Y-%m-%d'),
            litros,
            precio_por_litro,
            costo,
            odometro_actual,
            km_por_litro,
            "Importado desde Excel",
            now_ca().isoformat()
        ))
        
        logger.info(f"✅ Registro insertado: {placa} - {fecha} - {litros}L - ₡{costo}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error insertando registro para {registro.get('placa', 'N/A')}: {e}")
        return False

def main():
    """Función principal"""
    archivo_excel = "bitacora_nueva_2025-09-02.xlsx"
    
    logger.info("🚀 === INICIANDO IMPORTACIÓN DE COMBUSTIBLE ===")
    
    # Verificar que el archivo exista
    if not os.path.exists(archivo_excel):
        logger.error(f"❌ Archivo no encontrado: {archivo_excel}")
        return
    
    # Leer archivo Excel
    df, sheet_name = leer_excel_combustible(archivo_excel)
    if df is None:
        logger.error("❌ No se pudo leer el archivo Excel")
        return
    
    logger.info(f"📊 Procesando hoja '{sheet_name}' con {len(df)} filas")
    
    # Mapear columnas
    registros_mapeados = mapear_columnas(df)
    if not registros_mapeados:
        logger.error("❌ No hay registros válidos para importar")
        return
    
    # Conectar a la base de datos
    conn = get_db_connection()
    if not conn:
        logger.error("❌ No se pudo conectar a la base de datos")
        return
    
    # Insertar registros
    exitosos = 0
    fallidos = 0
    
    logger.info(f"💾 Insertando {len(registros_mapeados)} registros...")
    
    for i, registro in enumerate(registros_mapeados):
        logger.info(f"🔄 Procesando registro {i+1}/{len(registros_mapeados)}: {registro.get('placa', 'N/A')}")
        
        if insertar_registro_combustible(conn, registro):
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
        logger.info("🎉 ¡Importación completada exitosamente!")
    else:
        logger.warning("⚠️ No se importaron registros")

if __name__ == "__main__":
    main()