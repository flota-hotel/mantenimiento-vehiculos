#!/usr/bin/env python3
"""
Script para cargar todos los datos CSV en la base de datos
"""

import sqlite3
import csv
import os
from datetime import datetime

DATABASE_PATH = "vehicular_system.db"

def init_database():
    """Inicializar base de datos con todas las tablas"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Tabla Vehiculos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT UNIQUE NOT NULL,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            ano INTEGER NOT NULL,
            color TEXT NOT NULL,
            propietario TEXT NOT NULL,
            poliza TEXT,
            seguro TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            km_inicial INTEGER DEFAULT 0
        )
    ''')
    
    # Tabla Mantenimientos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mantenimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL,
            placa TEXT NOT NULL,
            tipo TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            costo REAL NOT NULL,
            kilometraje INTEGER,
            proximo_km INTEGER,
            proxima_fecha DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (placa) REFERENCES vehiculos (placa)
        )
    ''')
    
    # Tabla Combustible
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS combustible (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL,
            placa TEXT NOT NULL,
            litros REAL NOT NULL,
            costo REAL NOT NULL,
            kilometraje INTEGER,
            estacion TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (placa) REFERENCES vehiculos (placa)
        )
    ''')
    
    # Tabla Bitacora
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bitacora (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT NOT NULL,
            chofer TEXT NOT NULL,
            fecha_salida TIMESTAMP NOT NULL,
            km_salida INTEGER NOT NULL,
            nivel_combustible_salida TEXT,
            estado_vehiculo_salida TEXT,
            fecha_retorno TIMESTAMP,
            km_retorno INTEGER,
            nivel_combustible_retorno TEXT,
            estado_vehiculo_retorno TEXT,
            observaciones TEXT,
            estado TEXT DEFAULT 'en_curso',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (placa) REFERENCES vehiculos (placa)
        )
    ''')
    
    # Tabla Config Alertas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_destino TEXT NOT NULL,
            alertas_mantenimiento INTEGER DEFAULT 1,
            alertas_polizas INTEGER DEFAULT 1,
            alertas_rtv INTEGER DEFAULT 1,
            alertas_revisiones INTEGER DEFAULT 1,
            alertas_combustible INTEGER DEFAULT 1,
            alertas_bitacora INTEGER DEFAULT 1,
            dias_anticipacion_polizas INTEGER DEFAULT 15,
            dias_anticipacion_rtv INTEGER DEFAULT 20,
            dias_anticipacion_mantenimiento INTEGER DEFAULT 10,
            km_diferencia_alerta INTEGER DEFAULT 5,
            activo INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla Historial Alertas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_alerta TEXT NOT NULL,
            vehiculo_placa TEXT,
            destinatario_email TEXT NOT NULL,
            asunto TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            estado TEXT DEFAULT 'enviado',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla Polizas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS polizas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_poliza TEXT,
            placa TEXT NOT NULL,
            aseguradora TEXT,
            fecha_inicio DATE,
            fecha_vencimiento DATE NOT NULL,
            tipo_cobertura TEXT,
            estado TEXT DEFAULT 'Vigente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (placa) REFERENCES vehiculos (placa)
        )
    ''')
    
    # Tabla Revisiones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS revisiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP NOT NULL,
            placa TEXT NOT NULL,
            inspector TEXT NOT NULL,
            estado_motor TEXT,
            estado_frenos TEXT,
            estado_luces TEXT,
            estado_llantas TEXT,
            estado_carroceria TEXT,
            observaciones TEXT,
            aprobado INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            luces_delanteras INTEGER DEFAULT 1,
            luces_traseras INTEGER DEFAULT 1,
            luces_direccionales INTEGER DEFAULT 1,
            luces_freno INTEGER DEFAULT 1,
            luces_reversa INTEGER DEFAULT 1,
            espejos_laterales INTEGER DEFAULT 1,
            espejo_retrovisor INTEGER DEFAULT 1,
            limpiaparabrisas INTEGER DEFAULT 1,
            cinturones INTEGER DEFAULT 1,
            bocina INTEGER DEFAULT 1,
            nivel_combustible TEXT,
            kilometraje INTEGER,
            FOREIGN KEY (placa) REFERENCES vehiculos (placa)
        )
    ''')
    
    # Tabla RTV
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rtv (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_cita TEXT,
            placa TEXT NOT NULL,
            fecha_vencimiento DATE NOT NULL,
            estado TEXT DEFAULT 'Vigente',
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (placa) REFERENCES vehiculos (placa)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada")

def clear_all_tables():
    """Limpiar todas las tablas antes de cargar nuevos datos"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    tables = ['historial_alertas', 'config_alertas', 'bitacora', 'combustible', 
              'mantenimientos', 'revisiones', 'rtv', 'polizas', 'vehiculos']
    
    for table in tables:
        try:
            cursor.execute(f'DELETE FROM {table}')
            print(f"✅ Tabla {table} limpiada")
        except Exception as e:
            print(f"⚠️ Error limpiando tabla {table}: {e}")
    
    conn.commit()
    conn.close()

def load_vehiculos():
    """Cargar datos de vehículos"""
    if not os.path.exists('vehiculos.csv'):
        print("⚠️ vehiculos.csv no encontrado")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    with open('vehiculos.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
                cursor.execute('''
                    INSERT INTO vehiculos 
                    (id, placa, marca, modelo, ano, color, propietario, poliza, seguro, 
                     created_at, updated_at, km_inicial)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('id'),
                    row.get('placa'),
                    row.get('marca'),
                    row.get('modelo'),
                    row.get('ano'),
                    row.get('color'),
                    row.get('propietario'),
                    row.get('poliza', ''),
                    row.get('seguro', ''),
                    row.get('created_at'),
                    row.get('updated_at'),
                    row.get('km_inicial', 0)
                ))
                count += 1
            except Exception as e:
                print(f"Error en vehículo {row.get('placa')}: {e}")
    
    conn.commit()
    conn.close()
    print(f"✅ {count} vehículos cargados")

def load_combustible():
    """Cargar datos de combustible"""
    if not os.path.exists('combustible.csv'):
        print("⚠️ combustible.csv no encontrado")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    with open('combustible.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
                cursor.execute('''
                    INSERT INTO combustible 
                    (id, fecha, placa, litros, costo, kilometraje, estacion, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('id'),
                    row.get('fecha'),
                    row.get('placa'),
                    row.get('litros'),
                    row.get('costo'),
                    row.get('kilometraje'),
                    row.get('estacion', ''),
                    row.get('created_at')
                ))
                count += 1
            except Exception as e:
                print(f"Error en combustible {row.get('id')}: {e}")
    
    conn.commit()
    conn.close()
    print(f"✅ {count} registros de combustible cargados")

def load_bitacora():
    """Cargar datos de bitácora"""
    if not os.path.exists('bitacora.csv'):
        print("⚠️ bitacora.csv no encontrado")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    with open('bitacora.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
                cursor.execute('''
                    INSERT INTO bitacora 
                    (id, placa, chofer, fecha_salida, km_salida, nivel_combustible_salida,
                     estado_vehiculo_salida, fecha_retorno, km_retorno, nivel_combustible_retorno,
                     estado_vehiculo_retorno, observaciones, estado, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('id'),
                    row.get('placa'),
                    row.get('chofer'),
                    row.get('fecha_salida'),
                    row.get('km_salida'),
                    row.get('nivel_combustible_salida'),
                    row.get('estado_vehiculo_salida'),
                    row.get('fecha_retorno') if row.get('fecha_retorno') else None,
                    row.get('km_retorno') if row.get('km_retorno') else None,
                    row.get('nivel_combustible_retorno'),
                    row.get('estado_vehiculo_retorno'),
                    row.get('observaciones', ''),
                    row.get('estado', 'completado'),
                    row.get('created_at')
                ))
                count += 1
            except Exception as e:
                print(f"Error en bitácora {row.get('id')}: {e}")
    
    conn.commit()
    conn.close()
    print(f"✅ {count} registros de bitácora cargados")

def load_mantenimientos():
    """Cargar datos de mantenimientos"""
    if not os.path.exists('mantenimientos.csv'):
        print("⚠️ mantenimientos.csv no encontrado")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    with open('mantenimientos.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
                cursor.execute('''
                    INSERT INTO mantenimientos 
                    (id, fecha, placa, tipo, descripcion, costo, kilometraje, 
                     proximo_km, proxima_fecha, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('id'),
                    row.get('fecha'),
                    row.get('placa'),
                    row.get('tipo'),
                    row.get('descripcion'),
                    row.get('costo'),
                    row.get('kilometraje'),
                    row.get('proximo_km') if row.get('proximo_km') else None,
                    row.get('proxima_fecha') if row.get('proxima_fecha') else None,
                    row.get('created_at')
                ))
                count += 1
            except Exception as e:
                print(f"Error en mantenimiento {row.get('id')}: {e}")
    
    conn.commit()
    conn.close()
    print(f"✅ {count} mantenimientos cargados")

def load_polizas():
    """Cargar datos de pólizas"""
    if not os.path.exists('polizas.csv'):
        print("⚠️ polizas.csv no encontrado")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    with open('polizas.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
                cursor.execute('''
                    INSERT INTO polizas 
                    (id, numero_poliza, placa, aseguradora, fecha_inicio, 
                     fecha_vencimiento, tipo_cobertura, estado, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('id'),
                    row.get('numero_poliza'),
                    row.get('placa'),
                    row.get('aseguradora'),
                    row.get('fecha_inicio'),
                    row.get('fecha_vencimiento'),
                    row.get('tipo_cobertura'),
                    row.get('estado', 'Vigente'),
                    row.get('created_at')
                ))
                count += 1
            except Exception as e:
                print(f"Error en póliza {row.get('id')}: {e}")
    
    conn.commit()
    conn.close()
    print(f"✅ {count} pólizas cargadas")

def load_revisiones():
    """Cargar datos de revisiones"""
    if not os.path.exists('revisiones.csv'):
        print("⚠️ revisiones.csv no encontrado")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    with open('revisiones.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
                cursor.execute('''
                    INSERT INTO revisiones 
                    (id, fecha, placa, inspector, estado_motor, estado_frenos, estado_luces,
                     estado_llantas, estado_carroceria, observaciones, aprobado, created_at,
                     luces_delanteras, luces_traseras, luces_direccionales, luces_freno,
                     luces_reversa, espejos_laterales, espejo_retrovisor, limpiaparabrisas,
                     cinturones, bocina, nivel_combustible, kilometraje)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('id'),
                    row.get('fecha'),
                    row.get('placa'),
                    row.get('inspector'),
                    row.get('estado_motor'),
                    row.get('estado_frenos'),
                    row.get('estado_luces'),
                    row.get('estado_llantas'),
                    row.get('estado_carroceria'),
                    row.get('observaciones', ''),
                    row.get('aprobado', 1),
                    row.get('created_at'),
                    row.get('luces_delanteras', 1),
                    row.get('luces_traseras', 1),
                    row.get('luces_direccionales', 1),
                    row.get('luces_freno', 1),
                    row.get('luces_reversa', 1),
                    row.get('espejos_laterales', 1),
                    row.get('espejo_retrovisor', 1),
                    row.get('limpiaparabrisas', 1),
                    row.get('cinturones', 1),
                    row.get('bocina', 1),
                    row.get('nivel_combustible'),
                    row.get('kilometraje')
                ))
                count += 1
            except Exception as e:
                print(f"Error en revisión {row.get('id')}: {e}")
    
    conn.commit()
    conn.close()
    print(f"✅ {count} revisiones cargadas")

def load_rtv():
    """Cargar datos de RTV"""
    if not os.path.exists('rtv.csv'):
        print("⚠️ rtv.csv no encontrado")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    with open('rtv.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
                cursor.execute('''
                    INSERT INTO rtv 
                    (id, numero_cita, placa, fecha_vencimiento, estado, observaciones, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('id'),
                    row.get('numero_cita'),
                    row.get('placa'),
                    row.get('fecha_vencimiento'),
                    row.get('estado', 'Vigente'),
                    row.get('observaciones', ''),
                    row.get('created_at')
                ))
                count += 1
            except Exception as e:
                print(f"Error en RTV {row.get('id')}: {e}")
    
    conn.commit()
    conn.close()
    print(f"✅ {count} RTVs cargados")

def load_config_alertas():
    """Cargar configuración de alertas"""
    if not os.path.exists('config_alertas.csv'):
        print("⚠️ config_alertas.csv no encontrado")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    with open('config_alertas.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
                # Cambiar el email a tech@arenalmanoa.com
                email_destino = 'tech@arenalmanoa.com'
                
                cursor.execute('''
                    INSERT INTO config_alertas 
                    (id, email_destino, alertas_mantenimiento, alertas_polizas, alertas_rtv,
                     alertas_revisiones, alertas_combustible, alertas_bitacora,
                     dias_anticipacion_polizas, dias_anticipacion_rtv, 
                     dias_anticipacion_mantenimiento, km_diferencia_alerta, activo,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('id'),
                    email_destino,  # Email cambiado
                    row.get('alertas_mantenimiento', 1),
                    row.get('alertas_polizas', 1),
                    row.get('alertas_rtv', 1),
                    row.get('alertas_revisiones', 1),
                    row.get('alertas_combustible', 1),
                    row.get('alertas_bitacora', 1),
                    row.get('dias_anticipacion_polizas', 15),
                    row.get('dias_anticipacion_rtv', 20),
                    row.get('dias_anticipacion_mantenimiento', 10),
                    row.get('km_diferencia_alerta', 5),
                    row.get('activo', 1),
                    row.get('created_at'),
                    row.get('updated_at')
                ))
                count += 1
            except Exception as e:
                print(f"Error en config_alertas {row.get('id')}: {e}")
    
    conn.commit()
    conn.close()
    print(f"✅ {count} configuraciones de alertas cargadas (email: tech@arenalmanoa.com)")

def load_historial_alertas():
    """Cargar historial de alertas"""
    if not os.path.exists('historial_alertas.csv'):
        print("⚠️ historial_alertas.csv no encontrado")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    with open('historial_alertas.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
                cursor.execute('''
                    INSERT INTO historial_alertas 
                    (id, tipo_alerta, vehiculo_placa, destinatario_email, asunto, 
                     mensaje, estado, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('id'),
                    row.get('tipo_alerta'),
                    row.get('vehiculo_placa'),
                    row.get('destinatario_email'),
                    row.get('asunto'),
                    row.get('mensaje'),
                    row.get('estado', 'enviado'),
                    row.get('created_at')
                ))
                count += 1
            except Exception as e:
                print(f"Error en historial_alertas {row.get('id')}: {e}")
    
    conn.commit()
    conn.close()
    print(f"✅ {count} alertas históricas cargadas")

def main():
    """Función principal"""
    print("=" * 60)
    print("🚀 CARGA DE DATOS CSV AL SISTEMA VEHICULAR")
    print("=" * 60)
    
    # Inicializar base de datos
    init_database()
    
    # Limpiar tablas existentes
    print("\n🧹 Limpiando datos existentes...")
    clear_all_tables()
    
    # Cargar datos en orden
    print("\n📥 Cargando datos...")
    load_vehiculos()
    load_combustible()
    load_bitacora()
    load_mantenimientos()
    load_polizas()
    load_revisiones()
    load_rtv()
    load_config_alertas()
    load_historial_alertas()
    
    print("\n" + "=" * 60)
    print("✅ TODOS LOS DATOS HAN SIDO CARGADOS EXITOSAMENTE")
    print("📧 Email de alertas configurado a: tech@arenalmanoa.com")
    print("=" * 60)

if __name__ == "__main__":
    main()
