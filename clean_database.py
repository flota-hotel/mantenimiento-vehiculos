#!/usr/bin/env python3
"""
Script de Limpieza Completa de Base de Datos
Elimina todos los datos de prueba y deja la base limpia para producción
"""

import sqlite3
import os
import json
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_current_data(db_path):
    """Crear backup de los datos actuales antes de limpiar"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        backup_data = {
            "backup_info": {
                "timestamp": datetime.now().isoformat(),
                "purpose": "Pre-cleanup backup of test data",
                "database_path": db_path
            },
            "data": {}
        }
        
        # Obtener todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Backup cada tabla
        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            # Obtener nombres de columnas
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Convertir a lista de diccionarios
            table_data = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    row_dict[columns[i]] = value
                table_data.append(row_dict)
            
            backup_data["data"][table] = {
                "columns": columns,
                "rows": table_data,
                "count": len(table_data)
            }
        
        conn.close()
        
        # Guardar backup
        backup_filename = f"pre_cleanup_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = os.path.join(os.path.dirname(db_path), "backups", backup_filename)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"✅ Backup creado: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"❌ Error creando backup: {e}")
        return None

def show_current_data(db_path):
    """Mostrar datos actuales antes de limpiar"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print("📊 DATOS ACTUALES EN LA BASE DE DATOS")
        print("="*60)
        
        tables = ['vehiculos', 'mantenimientos', 'combustible', 'revisiones', 'polizas', 'rtv', 'bitacora']
        
        total_records = 0
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_records += count
                print(f"📋 {table.upper():<15}: {count:>3} registros")
                
                if count > 0 and count <= 5:  # Mostrar detalles si hay pocos registros
                    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                    rows = cursor.fetchall()
                    for i, row in enumerate(rows, 1):
                        print(f"    {i}. {str(row)[:80]}{'...' if len(str(row)) > 80 else ''}")
                    if count > 3:
                        print(f"    ... y {count-3} más")
                        
            except sqlite3.Error as e:
                print(f"📋 {table.upper():<15}: ERROR - {e}")
        
        print("-" * 60)
        print(f"📊 TOTAL REGISTROS: {total_records}")
        print("="*60)
        
        conn.close()
        return total_records
        
    except Exception as e:
        logger.error(f"❌ Error mostrando datos: {e}")
        return 0

def clean_all_data(db_path):
    """Limpiar todos los datos de la base de datos"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🧹 INICIANDO LIMPIEZA COMPLETA...")
        
        # Tablas a limpiar en orden (respetando llaves foráneas)
        tables_to_clean = [
            'bitacora',      # Registros de bitácora
            'rtv',           # Revisiones técnicas
            'polizas',       # Pólizas de seguros
            'revisiones',    # Revisiones generales
            'combustible',   # Registros de combustible
            'mantenimientos', # Mantenimientos
            'vehiculos'      # Vehículos (base de todo)
        ]
        
        deleted_counts = {}
        
        for table in tables_to_clean:
            try:
                # Contar registros antes
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                before_count = cursor.fetchone()[0]
                
                if before_count > 0:
                    # Eliminar todos los registros
                    cursor.execute(f"DELETE FROM {table}")
                    
                    # Resetear el autoincrement
                    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                    
                    deleted_counts[table] = before_count
                    print(f"  ✅ {table.upper()}: {before_count} registros eliminados")
                else:
                    print(f"  ⚪ {table.upper()}: ya estaba vacía")
                    
            except sqlite3.Error as e:
                print(f"  ❌ {table.upper()}: ERROR - {e}")
        
        # Confirmar cambios
        conn.commit()
        conn.close()
        
        print("\n✅ LIMPIEZA COMPLETADA")
        total_deleted = sum(deleted_counts.values())
        print(f"📊 Total de registros eliminados: {total_deleted}")
        
        return deleted_counts
        
    except Exception as e:
        logger.error(f"❌ Error limpiando base de datos: {e}")
        return {}

def verify_clean_database(db_path):
    """Verificar que la base de datos esté completamente limpia"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🔍 VERIFICANDO BASE DE DATOS LIMPIA...")
        
        tables = ['vehiculos', 'mantenimientos', 'combustible', 'revisiones', 'polizas', 'rtv', 'bitacora']
        
        all_clean = True
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                if count == 0:
                    print(f"  ✅ {table.upper()}: LIMPIA (0 registros)")
                else:
                    print(f"  ❌ {table.upper()}: NO LIMPIA ({count} registros)")
                    all_clean = False
                    
            except sqlite3.Error as e:
                print(f"  ❌ {table.upper()}: ERROR - {e}")
                all_clean = False
        
        conn.close()
        
        if all_clean:
            print("\n🎉 ¡BASE DE DATOS COMPLETAMENTE LIMPIA!")
            print("📦 Lista para recibir datos reales de producción")
        else:
            print("\n⚠️ ADVERTENCIA: La base de datos no está completamente limpia")
            
        return all_clean
        
    except Exception as e:
        logger.error(f"❌ Error verificando base de datos: {e}")
        return False

def main():
    """Función principal"""
    db_path = os.path.join(os.getcwd(), "vehicular_system.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    print("🚀 SCRIPT DE LIMPIEZA COMPLETA DE BASE DE DATOS")
    print("=" * 60)
    print("⚠️  ADVERTENCIA: Este script eliminará TODOS los datos actuales")
    print("📦 Preparará la base de datos para datos reales de producción")
    print("=" * 60)
    
    # 1. Mostrar datos actuales
    current_records = show_current_data(db_path)
    
    if current_records == 0:
        print("\n✅ La base de datos ya está limpia")
        return True
    
    # 2. Crear backup de datos actuales
    print(f"\n💾 Creando backup de {current_records} registros actuales...")
    backup_path = backup_current_data(db_path)
    
    if not backup_path:
        print("❌ Error creando backup. Abortando limpieza por seguridad.")
        return False
    
    # 3. Confirmar limpieza
    print(f"\n⚠️  ¿Continuar con la limpieza completa?")
    print("   - Eliminará todos los vehículos de prueba")
    print("   - Eliminará todos los registros de mantenimientos")
    print("   - Eliminará toda la bitácora")
    print("   - La base quedará lista para datos reales")
    print(f"   - Backup guardado en: {backup_path}")
    
    # 4. Ejecutar limpieza
    print(f"\n🧹 Ejecutando limpieza automática...")
    deleted_counts = clean_all_data(db_path)
    
    if not deleted_counts:
        print("❌ Error en la limpieza")
        return False
    
    # 5. Verificar que esté limpia
    is_clean = verify_clean_database(db_path)
    
    if is_clean:
        print("\n🎯 RESULTADO:")
        print("✅ Base de datos limpia y lista para producción")
        print("📦 Puedes empezar a agregar los datos reales")
        print(f"💾 Backup de datos anteriores: {backup_path}")
    
    return is_clean

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)