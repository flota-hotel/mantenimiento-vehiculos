#!/usr/bin/env python3
"""
Migración para agregar nuevos campos eléctricos a la tabla revisiones
"""

import sqlite3
import os

def migrate_database():
    db_path = "vehicular_system.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lista de nuevos campos eléctricos a agregar
        new_fields = [
            "luces_delanteras INTEGER DEFAULT 1",
            "luces_traseras INTEGER DEFAULT 1", 
            "luces_direccionales INTEGER DEFAULT 1",
            "luces_freno INTEGER DEFAULT 1",
            "luces_reversa INTEGER DEFAULT 1",
            "espejos_laterales INTEGER DEFAULT 1",
            "espejo_retrovisor INTEGER DEFAULT 1",
            "limpiaparabrisas INTEGER DEFAULT 1",
            "cinturones INTEGER DEFAULT 1", 
            "bocina INTEGER DEFAULT 1",
            "nivel_combustible TEXT DEFAULT 'lleno'"
        ]
        
        # Verificar si las columnas ya existen
        cursor.execute("PRAGMA table_info(revisiones)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 Columnas existentes: {existing_columns}")
        
        # Agregar solo las columnas que no existen
        for field in new_fields:
            field_name = field.split()[0]
            if field_name not in existing_columns:
                alter_query = f"ALTER TABLE revisiones ADD COLUMN {field}"
                print(f"🔧 Agregando columna: {field_name}")
                cursor.execute(alter_query)
            else:
                print(f"✅ Columna ya existe: {field_name}")
        
        conn.commit()
        
        # Verificar el esquema actualizado
        cursor.execute("PRAGMA table_info(revisiones)")
        updated_columns = [col[1] for col in cursor.fetchall()]
        print(f"✅ Esquema actualizado: {updated_columns}")
        
        conn.close()
        print("🎉 Migración completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error en la migración: {e}")
        return False

if __name__ == "__main__":
    migrate_database()