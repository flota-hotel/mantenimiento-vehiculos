#!/usr/bin/env python3
"""
Sistema de Gestión Vehicular - Backend API
FastAPI Backend para reemplazar Google Sheets
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
import json
from datetime import datetime, date
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(title="Sistema de Gestión Vehicular", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base de datos SQLite
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
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    
    # Tabla Revisiones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS revisiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL,
            placa TEXT NOT NULL,
            inspector TEXT NOT NULL,
            estado_motor TEXT NOT NULL,
            estado_frenos TEXT NOT NULL,
            estado_luces TEXT NOT NULL,
            estado_llantas TEXT NOT NULL,
            estado_carroceria TEXT NOT NULL,
            observaciones TEXT,
            aprobado BOOLEAN NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (placa) REFERENCES vehiculos (placa)
        )
    ''')
    
    # Tabla Polizas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS polizas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_poliza TEXT UNIQUE NOT NULL,
            placa TEXT NOT NULL,
            aseguradora TEXT NOT NULL,
            fecha_inicio DATE NOT NULL,
            fecha_vencimiento DATE NOT NULL,
            tipo_cobertura TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'Activa',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (placa) REFERENCES vehiculos (placa)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Base de datos inicializada correctamente")

# Modelos Pydantic
class VehiculoCreate(BaseModel):
    placa: str
    marca: str
    modelo: str
    ano: int
    color: str
    propietario: str
    poliza: Optional[str] = None
    seguro: Optional[str] = None

class VehiculoUpdate(BaseModel):
    marca: Optional[str] = None
    modelo: Optional[str] = None
    ano: Optional[int] = None
    color: Optional[str] = None
    propietario: Optional[str] = None
    poliza: Optional[str] = None
    seguro: Optional[str] = None

class MantenimientoCreate(BaseModel):
    fecha: str
    placa: str
    tipo: str
    descripcion: str
    costo: float
    kilometraje: Optional[int] = None

class CombustibleCreate(BaseModel):
    fecha: str
    placa: str
    litros: float
    costo: float
    kilometraje: Optional[int] = None
    estacion: Optional[str] = None

class RevisionCreate(BaseModel):
    fecha: str
    placa: str
    inspector: str
    estado_motor: str
    estado_frenos: str
    estado_luces: str
    estado_llantas: str
    estado_carroceria: str
    observaciones: Optional[str] = None
    aprobado: bool

class PolizaCreate(BaseModel):
    numero_poliza: str
    placa: str
    aseguradora: str
    fecha_inicio: str
    fecha_vencimiento: str
    tipo_cobertura: str
    estado: Optional[str] = "Activa"

# Utilidades de base de datos
def get_db_connection():
    """Obtener conexión a la base de datos"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def dict_from_row(row):
    """Convertir Row de SQLite a diccionario"""
    return dict(zip(row.keys(), row)) if row else None

# Inicializar base de datos al iniciar
init_database()

# ================================
# ENDPOINTS PRINCIPALES
# ================================

@app.get("/")
async def root():
    """Endpoint de prueba"""
    return {"message": "Sistema de Gestión Vehicular API", "status": "active"}

# ================================
# ENDPOINTS VEHÍCULOS
# ================================

@app.get("/vehiculos")
async def get_vehiculos():
    """Obtener todos los vehículos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vehiculos ORDER BY placa")
        vehiculos = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return {"success": True, "data": vehiculos}
    except Exception as e:
        logger.error(f"Error al obtener vehículos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vehiculos")
async def create_vehiculo(vehiculo: VehiculoCreate):
    """Crear un nuevo vehículo"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO vehiculos (placa, marca, modelo, ano, color, propietario, poliza, seguro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (vehiculo.placa, vehiculo.marca, vehiculo.modelo, vehiculo.ano, 
              vehiculo.color, vehiculo.propietario, vehiculo.poliza, vehiculo.seguro))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Vehículo creado exitosamente"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="La placa ya existe")
    except Exception as e:
        logger.error(f"Error al crear vehículo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/vehiculos/{placa}")
async def update_vehiculo(placa: str, vehiculo: VehiculoUpdate):
    """Actualizar un vehículo"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Construir query dinámicamente
        updates = []
        values = []
        
        for field, value in vehiculo.dict(exclude_unset=True).items():
            if value is not None:
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        values.append(placa)
        query = f"UPDATE vehiculos SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE placa = ?"
        
        cursor.execute(query, values)
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Vehículo no encontrado")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Vehículo actualizado exitosamente"}
    except Exception as e:
        logger.error(f"Error al actualizar vehículo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/vehiculos/{placa}")
async def delete_vehiculo(placa: str):
    """Eliminar un vehículo"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM vehiculos WHERE placa = ?", (placa,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Vehículo no encontrado")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Vehículo eliminado exitosamente"}
    except Exception as e:
        logger.error(f"Error al eliminar vehículo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ENDPOINTS MANTENIMIENTOS
# ================================

@app.get("/mantenimientos")
async def get_mantenimientos():
    """Obtener todos los mantenimientos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mantenimientos ORDER BY fecha DESC")
        mantenimientos = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return {"success": True, "data": mantenimientos}
    except Exception as e:
        logger.error(f"Error al obtener mantenimientos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mantenimientos")
async def create_mantenimiento(mantenimiento: MantenimientoCreate):
    """Crear un nuevo mantenimiento"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO mantenimientos (fecha, placa, tipo, descripcion, costo, kilometraje)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (mantenimiento.fecha, mantenimiento.placa, mantenimiento.tipo,
              mantenimiento.descripcion, mantenimiento.costo, mantenimiento.kilometraje))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Mantenimiento creado exitosamente"}
    except Exception as e:
        logger.error(f"Error al crear mantenimiento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/mantenimientos/{mantenimiento_id}")
async def delete_mantenimiento(mantenimiento_id: int):
    """Eliminar un mantenimiento"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM mantenimientos WHERE id = ?", (mantenimiento_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Mantenimiento no encontrado")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Mantenimiento eliminado exitosamente"}
    except Exception as e:
        logger.error(f"Error al eliminar mantenimiento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ENDPOINTS COMBUSTIBLE
# ================================

@app.get("/combustible")
async def get_combustible():
    """Obtener todos los registros de combustible"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM combustible ORDER BY fecha DESC")
        combustible = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return {"success": True, "data": combustible}
    except Exception as e:
        logger.error(f"Error al obtener combustible: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/combustible")
async def create_combustible(combustible: CombustibleCreate):
    """Crear un nuevo registro de combustible"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO combustible (fecha, placa, litros, costo, kilometraje, estacion)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (combustible.fecha, combustible.placa, combustible.litros,
              combustible.costo, combustible.kilometraje, combustible.estacion))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Registro de combustible creado exitosamente"}
    except Exception as e:
        logger.error(f"Error al crear registro de combustible: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/combustible/{combustible_id}")
async def delete_combustible(combustible_id: int):
    """Eliminar un registro de combustible"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM combustible WHERE id = ?", (combustible_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Registro de combustible no encontrado")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Registro de combustible eliminado exitosamente"}
    except Exception as e:
        logger.error(f"Error al eliminar registro de combustible: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ENDPOINTS REVISIONES
# ================================

@app.get("/revisiones")
async def get_revisiones():
    """Obtener todas las revisiones"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM revisiones ORDER BY fecha DESC")
        revisiones = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return {"success": True, "data": revisiones}
    except Exception as e:
        logger.error(f"Error al obtener revisiones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/revisiones")
async def create_revision(revision: RevisionCreate):
    """Crear una nueva revisión"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO revisiones (fecha, placa, inspector, estado_motor, estado_frenos,
                                  estado_luces, estado_llantas, estado_carroceria, 
                                  observaciones, aprobado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (revision.fecha, revision.placa, revision.inspector, revision.estado_motor,
              revision.estado_frenos, revision.estado_luces, revision.estado_llantas,
              revision.estado_carroceria, revision.observaciones, revision.aprobado))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Revisión creada exitosamente"}
    except Exception as e:
        logger.error(f"Error al crear revisión: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/revisiones/{revision_id}")
async def delete_revision(revision_id: int):
    """Eliminar una revisión"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM revisiones WHERE id = ?", (revision_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Revisión no encontrada")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Revisión eliminada exitosamente"}
    except Exception as e:
        logger.error(f"Error al eliminar revisión: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ENDPOINTS PÓLIZAS
# ================================

@app.get("/polizas")
async def get_polizas():
    """Obtener todas las pólizas"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM polizas ORDER BY fecha_vencimiento")
        polizas = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return {"success": True, "data": polizas}
    except Exception as e:
        logger.error(f"Error al obtener pólizas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/polizas")
async def create_poliza(poliza: PolizaCreate):
    """Crear una nueva póliza"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO polizas (numero_poliza, placa, aseguradora, fecha_inicio,
                               fecha_vencimiento, tipo_cobertura, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (poliza.numero_poliza, poliza.placa, poliza.aseguradora,
              poliza.fecha_inicio, poliza.fecha_vencimiento, poliza.tipo_cobertura, poliza.estado))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Póliza creada exitosamente"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="El número de póliza ya existe")
    except Exception as e:
        logger.error(f"Error al crear póliza: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/polizas/{poliza_id}")
async def delete_poliza(poliza_id: int):
    """Eliminar una póliza"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM polizas WHERE id = ?", (poliza_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Póliza no encontrada")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Póliza eliminada exitosamente"}
    except Exception as e:
        logger.error(f"Error al eliminar póliza: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ENDPOINTS COMPATIBILIDAD (Google Apps Script format)
# ================================

@app.get("/exec")
@app.post("/exec")
async def exec_endpoint(action: str = Query(...), **params):
    """Endpoint de compatibilidad con el formato de Google Apps Script"""
    try:
        if action == "getVehiculos":
            return await get_vehiculos()
        elif action == "getMantenimientos":
            return await get_mantenimientos()
        elif action == "getCombustible":
            return await get_combustible()
        elif action == "getRevisiones":
            return await get_revisiones()
        elif action == "getPolizas":
            return await get_polizas()
        else:
            raise HTTPException(status_code=400, detail=f"Acción no soportada: {action}")
    except Exception as e:
        logger.error(f"Error en endpoint exec: {e}")
        return {"success": False, "error": str(e)}

# ================================
# ESTADÍSTICAS Y DASHBOARD
# ================================

@app.get("/stats")
async def get_stats():
    """Obtener estadísticas para el dashboard"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Contar totales
        cursor.execute("SELECT COUNT(*) as total FROM vehiculos")
        total_vehiculos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as total FROM mantenimientos WHERE fecha >= date('now', '-30 days')")
        mantenimientos_mes = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(costo) as total FROM combustible WHERE fecha >= date('now', '-30 days')")
        result = cursor.fetchone()
        gasto_combustible_mes = result[0] if result[0] else 0
        
        cursor.execute("SELECT COUNT(*) as total FROM revisiones WHERE aprobado = 0")
        revisiones_pendientes = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "success": True,
            "data": {
                "total_vehiculos": total_vehiculos,
                "mantenimientos_mes": mantenimientos_mes,
                "gasto_combustible_mes": round(gasto_combustible_mes, 2),
                "revisiones_pendientes": revisiones_pendientes
            }
        }
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")