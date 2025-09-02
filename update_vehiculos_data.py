#!/usr/bin/env python3
"""
Script para actualizar los datos de vehículos ya importados
Corrige marca y modelo usando los datos del Excel
"""

import pandas as pd
import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_vehiculos_data():
    """Actualizar datos de vehículos ya importados"""
    
    # Leer datos del Excel
    vehiculos_df = pd.read_excel("vehiculos.xlsx")
    
    # Normalizar nombres de columnas
    vehiculos_df.columns = [col.strip().lower().replace(' ', '_').replace('/', '_').replace('ñ', 'n') for col in vehiculos_df.columns]
    
    conn = sqlite3.connect("vehicular_system.db")
    cursor = conn.cursor()
    
    updated_count = 0
    
    for index, row in vehiculos_df.iterrows():
        try:
            placa = str(row.get('placa', '')).strip().upper()
            if not placa or placa == 'nan':
                continue
            
            # Extraer marca y modelo
            marca_modelo = str(row.get('marca_modelo', '')).strip()
            if marca_modelo and marca_modelo != 'nan':
                parts = marca_modelo.split(' ', 1)
                marca = parts[0]
                modelo = parts[1] if len(parts) > 1 else parts[0]
            else:
                marca = 'SIN MARCA'
                modelo = 'SIN MODELO'
            
            # Extraer año
            ano = None
            try:
                ano_val = row.get('ano', None)
                if pd.notna(ano_val):
                    ano = int(float(ano_val))
            except:
                ano = 2020  # Año por defecto
            
            # Extraer propietario/dueño
            dueno = str(row.get('dueno', '')).strip()
            propietario = 'Hotel'
            if dueno and dueno != 'nan':
                dueno_clean = dueno.replace('👤', '').strip()
                if dueno_clean:
                    propietario = dueno_clean
            
            # Extraer aseguradora
            aseguradora = str(row.get('aseguradora', '')).strip()
            seguro = None
            if aseguradora and aseguradora != 'nan':
                seguro = aseguradora
            
            # Actualizar vehículo
            cursor.execute('''
                UPDATE vehiculos 
                SET marca = ?, modelo = ?, ano = ?, propietario = ?, seguro = ?, 
                    updated_at = ?
                WHERE placa = ?
            ''', (marca, modelo, ano, propietario, seguro, datetime.now().isoformat(), placa))
            
            if cursor.rowcount > 0:
                updated_count += 1
                logger.info(f"✅ Actualizado: {placa} - {marca} {modelo} ({ano})")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando {placa}: {e}")
    
    conn.commit()
    conn.close()
    
    logger.info(f"🎯 Vehículos actualizados: {updated_count}")

if __name__ == "__main__":
    update_vehiculos_data()