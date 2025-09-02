#!/usr/bin/env python3
"""
Agregar registro específico de combustible para C173325
Basado en los datos mostrados en la interfaz web
"""

import sqlite3
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

def verificar_vehiculo_existe(conn, placa):
    """Verificar si el vehículo existe en la base de datos"""
    cursor = conn.cursor()
    cursor.execute("SELECT id, marca, modelo FROM vehiculos WHERE placa = ?", (placa,))
    result = cursor.fetchone()
    if result:
        logger.info(f"✅ Vehículo encontrado: {placa} - {result['marca']} {result['modelo']}")
        return True
    else:
        logger.error(f"❌ Vehículo {placa} no existe en la base de datos")
        return False

def verificar_combustible_existente(conn, placa, fecha):
    """Verificar si ya existe un registro de combustible para esta placa y fecha"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, litros, costo FROM combustible 
        WHERE placa = ? AND DATE(fecha) = DATE(?)
    """, (placa, fecha))
    result = cursor.fetchone()
    if result:
        logger.warning(f"⚠️ Ya existe registro de combustible para {placa} en {fecha}: {result['litros']}L - ₡{result['costo']}")
        return True
    return False

def agregar_registro_combustible():
    """Agregar el registro específico de combustible para C173325"""
    
    # Datos del registro según la imagen
    placa = "C173325"
    fecha = "2025-09-01"
    litros = 89.77
    precio_por_litro = 557
    costo = 50002
    odometro_actual = 74748
    proveedor = "Registro manual - Excel import"
    
    logger.info("🚀 === AGREGANDO REGISTRO DE COMBUSTIBLE C173325 ===")
    logger.info(f"📊 Datos: {placa} - {fecha} - {litros}L - ₡{precio_por_litro}/L - ₡{costo} - {odometro_actual}km")
    
    # Conectar a la base de datos
    conn = get_db_connection()
    if not conn:
        logger.error("❌ No se pudo conectar a la base de datos")
        return False
    
    try:
        # Verificar que el vehículo existe
        if not verificar_vehiculo_existe(conn, placa):
            conn.close()
            return False
        
        # Verificar si ya existe el registro
        if verificar_combustible_existente(conn, placa, fecha):
            respuesta = input("¿Desea continuar y crear un duplicado? (s/n): ")
            if respuesta.lower() != 's':
                logger.info("❌ Operación cancelada por el usuario")
                conn.close()
                return False
        
        # Insertar registro
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO combustible (
                placa, fecha, litros, costo, kilometraje, estacion, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            placa,
            fecha,
            litros,
            costo,
            odometro_actual,
            proveedor,
            now_ca().isoformat()
        ))
        
        # Obtener el ID del registro insertado
        combustible_id = cursor.lastrowid
        
        # Guardar cambios
        conn.commit()
        
        logger.info(f"✅ Registro de combustible insertado exitosamente")
        logger.info(f"   ID: {combustible_id}")
        logger.info(f"   Placa: {placa}")
        logger.info(f"   Fecha: {fecha}")
        logger.info(f"   Litros: {litros}L")
        logger.info(f"   Precio/L: ₡{precio_por_litro} (calculado: ₡{costo/litros:.2f})")
        logger.info(f"   Costo total: ₡{costo:,}")
        logger.info(f"   Odómetro: {odometro_actual:,} km")
        
        # Calcular km/L si es posible
        calcular_km_por_litro(conn, placa, combustible_id)
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error insertando registro: {e}")
        conn.rollback()
        conn.close()
        return False

def calcular_km_por_litro(conn, placa, combustible_id):
    """Calcular km/L basado en registros anteriores"""
    try:
        cursor = conn.cursor()
        
        # Obtener el registro actual
        cursor.execute("""
            SELECT * FROM combustible 
            WHERE id = ?
        """, (combustible_id,))
        registro_actual = cursor.fetchone()
        
        # Obtener el registro anterior más reciente
        cursor.execute("""
            SELECT * FROM combustible 
            WHERE placa = ? AND fecha < ? AND kilometraje > 0
            ORDER BY fecha DESC 
            LIMIT 1
        """, (placa, registro_actual['fecha']))
        registro_anterior = cursor.fetchone()
        
        if registro_anterior:
            km_recorridos = registro_actual['kilometraje'] - registro_anterior['kilometraje']
            if km_recorridos > 0 and registro_actual['litros'] > 0:
                km_por_litro = km_recorridos / registro_actual['litros']
                
                logger.info(f"📊 Km/L calculado: {km_por_litro:.2f} km/L")
                logger.info(f"   Km recorridos: {km_recorridos} km")
                logger.info(f"   Litros consumidos: {registro_actual['litros']} L")
                logger.info(f"   (Nota: No se puede guardar km/L - columna no existe en esquema actual)")
            else:
                logger.info("ℹ️ No se pudo calcular km/L - datos insuficientes")
        else:
            logger.info("ℹ️ No hay registro anterior para calcular km/L")
            
    except Exception as e:
        logger.warning(f"⚠️ Error calculando km/L: {e}")

def verificar_estado_final():
    """Verificar que el registro se agregó correctamente"""
    logger.info("🔍 === VERIFICACIÓN FINAL ===")
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Contar registros de combustible
        cursor.execute("SELECT COUNT(*) as total FROM combustible")
        total = cursor.fetchone()['total']
        logger.info(f"📊 Total de registros de combustible: {total}")
        
        # Mostrar registros de C173325
        cursor.execute("""
            SELECT fecha, litros, costo, kilometraje, estacion 
            FROM combustible 
            WHERE placa = 'C173325' 
            ORDER BY fecha DESC
        """)
        registros = cursor.fetchall()
        
        logger.info(f"📋 Registros de combustible para C173325: {len(registros)}")
        for reg in registros:
            precio_calc = reg['costo'] / reg['litros'] if reg['litros'] > 0 else 0
            logger.info(f"   {reg['fecha']}: {reg['litros']}L - ₡{reg['costo']:,} - {reg['kilometraje']:,}km - ₡{precio_calc:.0f}/L")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Error en verificación: {e}")

def main():
    """Función principal"""
    logger.info("🔥 === INICIANDO PROCESO DE AGREGAR COMBUSTIBLE ===")
    
    exito = agregar_registro_combustible()
    
    if exito:
        verificar_estado_final()
        logger.info("🎉 ¡Registro de combustible agregado exitosamente!")
        logger.info("💡 El dashboard debería mostrar ahora los datos de combustible")
    else:
        logger.error("❌ No se pudo agregar el registro de combustible")

if __name__ == "__main__":
    main()