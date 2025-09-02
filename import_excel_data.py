#!/usr/bin/env python3
"""
Importador de datos desde Excel
Carga vehículos y bitácora desde archivos Excel al sistema
"""

import pandas as pd
import sqlite3
import json
from datetime import datetime, date
import logging
import os
import asyncio
import sys

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar funciones del sistema principal
sys.path.append('.')
from main import get_db_connection, trigger_auto_backup

def analyze_excel_files():
    """Analizar los archivos Excel para entender su estructura"""
    logger.info("🔍 Analizando archivos Excel...")
    
    # Analizar vehículos
    try:
        vehiculos_df = pd.read_excel("vehiculos.xlsx")
        logger.info(f"📋 VEHÍCULOS - Filas: {len(vehiculos_df)}, Columnas: {len(vehiculos_df.columns)}")
        logger.info(f"📋 Columnas disponibles: {list(vehiculos_df.columns)}")
        logger.info("📋 Primeras 3 filas:")
        print(vehiculos_df.head(3).to_string())
        print()
    except Exception as e:
        logger.error(f"❌ Error leyendo vehículos.xlsx: {e}")
        return False
    
    # Analizar bitácora
    try:
        bitacora_df = pd.read_excel("bitacora_2025-09-01.xlsx")
        logger.info(f"📝 BITÁCORA - Filas: {len(bitacora_df)}, Columnas: {len(bitacora_df.columns)}")
        logger.info(f"📝 Columnas disponibles: {list(bitacora_df.columns)}")
        logger.info("📝 Primeras 3 filas:")
        print(bitacora_df.head(3).to_string())
        print()
    except Exception as e:
        logger.error(f"❌ Error leyendo bitacora_2025-09-01.xlsx: {e}")
        return False
    
    return vehiculos_df, bitacora_df

def normalize_column_names(df, mapping=None):
    """Normalizar nombres de columnas"""
    if mapping:
        df = df.rename(columns=mapping)
    
    # Limpiar nombres de columnas
    df.columns = [col.strip().lower().replace(' ', '_').replace('ñ', 'n') for col in df.columns]
    return df

def import_vehiculos(vehiculos_df):
    """Importar vehículos a la base de datos"""
    logger.info("🚗 Importando vehículos...")
    
    # Mapeo de columnas comunes según el archivo Excel
    column_mapping = {
        'Placa': 'placa',
        'Marca/Modelo': 'marca_modelo',
        'Año': 'ano',
        'Km Inicial': 'km_inicial',
        'Tipo': 'tipo',
        'Dueño': 'dueno',
        'Aseguradora': 'aseguradora',
        'Estado': 'estado_vehiculo',
        'Acciones': 'acciones'
    }
    
    vehiculos_df = normalize_column_names(vehiculos_df, column_mapping)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    imported_count = 0
    errors = []
    
    for index, row in vehiculos_df.iterrows():
        try:
            # Extraer datos con valores por defecto
            placa = str(row.get('placa', '')).strip().upper()
            marca = str(row.get('marca', '')).strip()
            modelo = str(row.get('modelo', '')).strip()
            
            if not placa or placa == 'nan':
                logger.warning(f"⚠️ Fila {index + 1}: Placa vacía, saltando...")
                continue
            
            # Validaciones básicas para campos requeridos (ya procesados arriba)
            
            # Datos básicos
            ano = None
            try:
                ano_val = row.get('ano', row.get('year', row.get('anio', None)))
                if pd.notna(ano_val):
                    ano = int(float(ano_val))
            except:
                ano = None
            
            color = str(row.get('color', 'BLANCO')).strip() if pd.notna(row.get('color')) else 'BLANCO'
            propietario = str(row.get('propietario', 'Hotel')).strip() if pd.notna(row.get('propietario')) else 'Hotel'
            
            # Seguros y pólizas
            seguro = str(row.get('seguro', '')).strip() if pd.notna(row.get('seguro')) else None
            poliza = str(row.get('poliza', '')).strip() if pd.notna(row.get('poliza')) else None
            
            # Fechas
            vencimiento_poliza = None
            vencimiento_rtv = None
            
            try:
                if pd.notna(row.get('vencimiento_poliza')):
                    venc_pol = row.get('vencimiento_poliza')
                    if isinstance(venc_pol, str):
                        vencimiento_poliza = datetime.strptime(venc_pol, '%Y-%m-%d').date().isoformat()
                    else:
                        vencimiento_poliza = venc_pol.date().isoformat()
            except:
                vencimiento_poliza = None
            
            try:
                if pd.notna(row.get('vencimiento_rtv')):
                    venc_rtv = row.get('vencimiento_rtv')
                    if isinstance(venc_rtv, str):
                        vencimiento_rtv = datetime.strptime(venc_rtv, '%Y-%m-%d').date().isoformat()
                    else:
                        vencimiento_rtv = venc_rtv.date().isoformat()
            except:
                vencimiento_rtv = None
            
            # Extraer marca y modelo de la columna combinada
            marca_modelo = str(row.get('marca_modelo', '')).strip()
            if marca_modelo and marca_modelo != 'nan':
                parts = marca_modelo.split(' ', 1)
                marca = parts[0]
                modelo = parts[1] if len(parts) > 1 else parts[0]
            else:
                marca = 'SIN MARCA'
                modelo = 'SIN MODELO'
            
            # Extraer propietario/dueño
            dueno = str(row.get('dueno', row.get('dueño', ''))).strip()
            if dueno and dueno != 'nan':
                # Limpiar emoji y texto innecesario
                dueno_clean = dueno.replace('👤', '').strip()
                if dueno_clean:
                    propietario = dueno_clean
            
            # Extraer aseguradora
            aseguradora = str(row.get('aseguradora', '')).strip()
            if aseguradora and aseguradora != 'nan':
                seguro = aseguradora
            
            # Insertar vehículo (usando solo columnas que existen)
            cursor.execute('''
                INSERT INTO vehiculos 
                (placa, marca, modelo, ano, color, propietario, seguro, poliza)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (placa, marca, modelo, ano, color, propietario, seguro, poliza))
            
            imported_count += 1
            logger.info(f"✅ Vehículo importado: {placa} - {marca} {modelo}")
            
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                errors.append(f"Fila {index + 1}: Vehículo {placa} ya existe")
                logger.warning(f"⚠️ Vehículo {placa} ya existe, saltando...")
            else:
                errors.append(f"Fila {index + 1}: Error de integridad - {e}")
                logger.error(f"❌ Error de integridad en fila {index + 1}: {e}")
        except Exception as e:
            errors.append(f"Fila {index + 1}: {e}")
            logger.error(f"❌ Error en fila {index + 1}: {e}")
    
    conn.commit()
    conn.close()
    
    logger.info(f"🎯 RESUMEN VEHÍCULOS:")
    logger.info(f"   ✅ Importados: {imported_count}")
    logger.info(f"   ❌ Errores: {len(errors)}")
    
    if errors:
        logger.info("📋 Errores encontrados:")
        for error in errors:
            logger.info(f"   • {error}")
    
    return imported_count, errors

def import_bitacora(bitacora_df, vehiculos_placas):
    """Importar bitácora a la base de datos"""
    logger.info("📝 Importando bitácora...")
    
    # Mapeo de columnas comunes
    column_mapping = {
        'Placa': 'placa',
        'Chofer': 'chofer',
        'Conductor': 'chofer',
        'Fecha Salida': 'fecha_salida',
        'Hora Salida': 'hora_salida',
        'Km Salida': 'km_salida',
        'Kilometraje Salida': 'km_salida',
        'Combustible Salida': 'combustible_salida',
        'Nivel Combustible Salida': 'combustible_salida',
        'Estado Salida': 'estado_salida',
        'Fecha Retorno': 'fecha_retorno',
        'Hora Retorno': 'hora_retorno',
        'Km Retorno': 'km_retorno',
        'Kilometraje Retorno': 'km_retorno',
        'Combustible Retorno': 'combustible_retorno',
        'Nivel Combustible Retorno': 'combustible_retorno',
        'Estado Retorno': 'estado_retorno',
        'Observaciones': 'observaciones',
        'Estado': 'estado'
    }
    
    bitacora_df = normalize_column_names(bitacora_df, column_mapping)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    imported_count = 0
    errors = []
    
    for index, row in bitacora_df.iterrows():
        try:
            # Extraer datos básicos
            placa = str(row.get('placa', '')).strip().upper()
            chofer = str(row.get('chofer', '')).strip()
            
            if not placa or placa == 'nan' or not chofer or chofer == 'nan':
                logger.warning(f"⚠️ Fila {index + 1}: Placa o chofer vacío, saltando...")
                continue
            
            # Verificar que el vehículo existe
            if placa not in vehiculos_placas:
                errors.append(f"Fila {index + 1}: Vehículo {placa} no encontrado")
                logger.warning(f"⚠️ Vehículo {placa} no encontrado, saltando...")
                continue
            
            # Procesar fechas y horas
            fecha_salida = None
            try:
                fecha_sal = row.get('fecha_salida')
                hora_sal = row.get('hora_salida', '08:00')
                
                if pd.notna(fecha_sal):
                    if isinstance(fecha_sal, str):
                        fecha_salida = datetime.strptime(f"{fecha_sal} {hora_sal}", '%Y-%m-%d %H:%M').isoformat()
                    else:
                        fecha_salida = datetime.combine(fecha_sal.date(), 
                                                       datetime.strptime(str(hora_sal), '%H:%M').time()).isoformat()
            except:
                fecha_salida = datetime.now().isoformat()
            
            fecha_retorno = None
            try:
                fecha_ret = row.get('fecha_retorno')
                hora_ret = row.get('hora_retorno', '17:00')
                
                if pd.notna(fecha_ret):
                    if isinstance(fecha_ret, str):
                        fecha_retorno = datetime.strptime(f"{fecha_ret} {hora_ret}", '%Y-%m-%d %H:%M').isoformat()
                    else:
                        fecha_retorno = datetime.combine(fecha_ret.date(), 
                                                        datetime.strptime(str(hora_ret), '%H:%M').time()).isoformat()
            except:
                fecha_retorno = None
            
            # Procesar kilometrajes
            km_salida = None
            km_retorno = None
            
            try:
                km_sal = row.get('km_salida')
                if pd.notna(km_sal):
                    km_salida = int(float(km_sal))
            except:
                km_salida = 0
            
            try:
                km_ret = row.get('km_retorno')
                if pd.notna(km_ret):
                    km_retorno = int(float(km_ret))
            except:
                km_retorno = None
            
            # Procesar otros campos
            combustible_salida = str(row.get('combustible_salida', '3/4')).strip() if pd.notna(row.get('combustible_salida')) else '3/4'
            combustible_retorno = str(row.get('combustible_retorno', '')).strip() if pd.notna(row.get('combustible_retorno')) else None
            estado_salida = str(row.get('estado_salida', 'bueno')).strip() if pd.notna(row.get('estado_salida')) else 'bueno'
            estado_retorno = str(row.get('estado_retorno', '')).strip() if pd.notna(row.get('estado_retorno')) else None
            observaciones = str(row.get('observaciones', '')).strip() if pd.notna(row.get('observaciones')) else None
            
            # Determinar estado del registro
            estado = 'completado' if fecha_retorno else 'en_curso'
            
            # Insertar registro
            cursor.execute('''
                INSERT INTO bitacora 
                (placa, chofer, fecha_salida, km_salida, nivel_combustible_salida, 
                 estado_vehiculo_salida, fecha_retorno, km_retorno, nivel_combustible_retorno,
                 estado_vehiculo_retorno, observaciones, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (placa, chofer, fecha_salida, km_salida, combustible_salida, estado_salida,
                  fecha_retorno, km_retorno, combustible_retorno, estado_retorno, observaciones, estado))
            
            imported_count += 1
            logger.info(f"✅ Bitácora importada: {placa} - {chofer} ({estado})")
            
        except Exception as e:
            errors.append(f"Fila {index + 1}: {e}")
            logger.error(f"❌ Error en fila {index + 1}: {e}")
    
    conn.commit()
    conn.close()
    
    logger.info(f"🎯 RESUMEN BITÁCORA:")
    logger.info(f"   ✅ Importados: {imported_count}")
    logger.info(f"   ❌ Errores: {len(errors)}")
    
    if errors:
        logger.info("📋 Errores encontrados:")
        for error in errors:
            logger.info(f"   • {error}")
    
    return imported_count, errors

def get_existing_vehiculos():
    """Obtener placas de vehículos existentes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT placa FROM vehiculos")
    placas = {row[0] for row in cursor.fetchall()}
    conn.close()
    return placas

async def main():
    """Función principal de importación"""
    logger.info("🚀 INICIANDO IMPORTACIÓN DESDE EXCEL")
    logger.info("=" * 60)
    
    # 1. Verificar archivos
    if not os.path.exists("vehiculos.xlsx"):
        logger.error("❌ Archivo vehiculos.xlsx no encontrado")
        return False
    
    if not os.path.exists("bitacora_2025-09-01.xlsx"):
        logger.error("❌ Archivo bitacora_2025-09-01.xlsx no encontrado")
        return False
    
    # 2. Analizar archivos
    result = analyze_excel_files()
    if not result:
        return False
    
    vehiculos_df, bitacora_df = result
    
    # 3. Obtener vehículos existentes
    existing_vehiculos = get_existing_vehiculos()
    logger.info(f"🚗 Vehículos existentes en DB: {len(existing_vehiculos)}")
    
    # 4. Importar vehículos
    vehiculos_imported, vehiculos_errors = import_vehiculos(vehiculos_df)
    
    # 5. Obtener placas actualizadas (incluye los recién importados)
    all_vehiculos = get_existing_vehiculos()
    
    # 6. Importar bitácora
    bitacora_imported, bitacora_errors = import_bitacora(bitacora_df, all_vehiculos)
    
    # 7. Backup automático
    if vehiculos_imported > 0 or bitacora_imported > 0:
        logger.info("💾 Ejecutando backup automático...")
        await trigger_auto_backup("excel_import")
    
    # 8. Resumen final
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESUMEN FINAL DE IMPORTACIÓN")
    logger.info("=" * 60)
    logger.info(f"🚗 Vehículos importados: {vehiculos_imported}")
    logger.info(f"📝 Registros de bitácora importados: {bitacora_imported}")
    logger.info(f"❌ Total errores: {len(vehiculos_errors) + len(bitacora_errors)}")
    
    if vehiculos_imported > 0 or bitacora_imported > 0:
        logger.info("✅ IMPORTACIÓN COMPLETADA EXITOSAMENTE")
        logger.info("🔄 Los datos están ahora disponibles en Railway")
        logger.info("💾 Backup automático ejecutado")
    else:
        logger.info("⚠️ No se importaron datos nuevos")
    
    return True

if __name__ == "__main__":
    # Instalar dependencia si es necesaria
    try:
        import pandas as pd
    except ImportError:
        logger.info("📦 Instalando pandas...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas", "openpyxl"])
        import pandas as pd
    
    # Ejecutar importación
    asyncio.run(main())