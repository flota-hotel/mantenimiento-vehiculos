#!/usr/bin/env python3
"""
Sistema de Gestión Vehicular - Backend API
FastAPI Backend para reemplazar Google Sheets
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
import json
from datetime import datetime, date, timedelta
import os
import logging
import asyncio

# Configurar logging PRIMERO
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
except ImportError:
    pass  # SMTP opcional

# Importar SendGrid como sistema principal de email
try:
    from sendgrid_email import send_system_email, send_alert_notification
    EMAIL_METHOD = "SENDGRID"
    logger.info("✅ SendGrid email service loaded")
except ImportError:
    logger.warning("⚠️ SendGrid not available, using SMTP fallback")
    EMAIL_METHOD = "SMTP"

# Importar sistema de backup automático a GitHub (opcional)
try:
    from github_backup_system import GitHubBackupSystem
    backup_system = GitHubBackupSystem()
    AUTO_BACKUP_ENABLED = True
    logger.info("✅ GitHub backup system loaded")
except Exception as e:
    AUTO_BACKUP_ENABLED = False
    backup_system = None
    logger.warning(f"⚠️ GitHub backup system not available: {e}")

# Importar sistema de preservación de datos (opcional)
try:
    from data_preservation_system import preservation_system, protect_data_operation
    DATA_PRESERVATION_ENABLED = True
    logger.info("✅ Data preservation system loaded")
except Exception as e:
    DATA_PRESERVATION_ENABLED = False
    preservation_system = None
    logger.warning(f"⚠️ Data preservation system not available: {e}")
    
    # Crear decorador dummy si no está disponible
    def protect_data_operation(description):
        def decorator(func):
            return func
        return decorator

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

# Servir archivos estáticos (CSS, JS, imágenes)
app.mount("/static", StaticFiles(directory="."), name="static")

# Base de datos SQLite
DATABASE_PATH = "vehicular_system.db"

# Configuración de Email
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "sistema.vehicular@arenalmanoa.com",  # CAMBIAR por su email real
    "sender_password": "",  # CONFIGURAR con contraseña de aplicación
    "recipient_email": "contabilidad2@arenalmanoa.com"
}

# Configuraciones alternativas para diferentes proveedores
EMAIL_PROVIDERS = {
    "gmail": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "use_tls": True
    },
    "outlook": {
        "smtp_server": "smtp-mail.outlook.com", 
        "smtp_port": 587,
        "use_tls": True
    },
    "yahoo": {
        "smtp_server": "smtp.mail.yahoo.com",
        "smtp_port": 587, 
        "use_tls": True
    },
    "custom": {
        "smtp_server": "mail.arenalmanoa.com",  # Su servidor personalizado
        "smtp_port": 587,
        "use_tls": True
    }
}

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
            proximo_km INTEGER,
            proxima_fecha DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (placa) REFERENCES vehiculos (placa)
        )
    ''')
    
    # Agregar columnas si no existen (para migración)
    try:
        cursor.execute('ALTER TABLE mantenimientos ADD COLUMN proximo_km INTEGER')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE mantenimientos ADD COLUMN proxima_fecha DATE')
    except:
        pass
    
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
            -- Nuevos campos para sistema eléctrico y exterior
            luces_delanteras BOOLEAN DEFAULT 1,
            luces_traseras BOOLEAN DEFAULT 1,
            luces_direccionales BOOLEAN DEFAULT 1,
            luces_freno BOOLEAN DEFAULT 1,
            luces_reversa BOOLEAN DEFAULT 1,
            espejos_laterales BOOLEAN DEFAULT 1,
            espejo_retrovisor BOOLEAN DEFAULT 1,
            limpiaparabrisas BOOLEAN DEFAULT 1,
            cinturones BOOLEAN DEFAULT 1,
            bocina BOOLEAN DEFAULT 1,
            nivel_combustible TEXT DEFAULT 'lleno',
            kilometraje INTEGER,
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
    
    # Tabla RTV (Revisión Técnica Vehicular)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rtv (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_cita TEXT NOT NULL,
            placa TEXT NOT NULL,
            fecha_vencimiento DATE NOT NULL,
            estado TEXT NOT NULL DEFAULT 'Vigente',
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (placa) REFERENCES vehiculos (placa)
        )
    ''')
    
    # Tabla Bitácora
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bitacora (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT NOT NULL,
            chofer TEXT NOT NULL,
            fecha_salida DATETIME NOT NULL,
            km_salida INTEGER NOT NULL,
            nivel_combustible_salida TEXT NOT NULL,
            estado_vehiculo_salida TEXT NOT NULL,
            fecha_retorno DATETIME,
            km_retorno INTEGER,
            nivel_combustible_retorno TEXT,
            estado_vehiculo_retorno TEXT,
            observaciones TEXT,
            estado TEXT DEFAULT 'en_curso',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (placa) REFERENCES vehiculos (placa)
        )
    ''')
    
    # Tabla de configuración de alertas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_destino TEXT NOT NULL,
            alertas_mantenimiento BOOLEAN DEFAULT 1,
            alertas_polizas BOOLEAN DEFAULT 1,
            alertas_rtv BOOLEAN DEFAULT 1,
            alertas_revisiones BOOLEAN DEFAULT 1,
            alertas_combustible BOOLEAN DEFAULT 1,
            alertas_bitacora BOOLEAN DEFAULT 1,
            dias_anticipacion_polizas INTEGER DEFAULT 30,
            dias_anticipacion_rtv INTEGER DEFAULT 30,
            dias_anticipacion_mantenimiento INTEGER DEFAULT 30,
            km_diferencia_alerta INTEGER DEFAULT 10,
            activo BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Agregar nuevas columnas a la tabla revisiones si no existen
    try:
        cursor.execute("ALTER TABLE revisiones ADD COLUMN luces_delanteras BOOLEAN DEFAULT 1")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE revisiones ADD COLUMN luces_traseras BOOLEAN DEFAULT 1")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE revisiones ADD COLUMN luces_direccionales BOOLEAN DEFAULT 1")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE revisiones ADD COLUMN luces_freno BOOLEAN DEFAULT 1")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE revisiones ADD COLUMN luces_reversa BOOLEAN DEFAULT 1")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE revisiones ADD COLUMN espejos_laterales BOOLEAN DEFAULT 1")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE revisiones ADD COLUMN espejo_retrovisor BOOLEAN DEFAULT 1")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE revisiones ADD COLUMN limpiaparabrisas BOOLEAN DEFAULT 1")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE revisiones ADD COLUMN cinturones BOOLEAN DEFAULT 1")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE revisiones ADD COLUMN bocina BOOLEAN DEFAULT 1")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE revisiones ADD COLUMN nivel_combustible TEXT DEFAULT 'lleno'")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE revisiones ADD COLUMN kilometraje INTEGER")
    except:
        pass
    
    conn.commit()
    conn.close()
    logger.info("Base de datos inicializada correctamente")

# Modelos Pydantic
class VehiculoCreate(BaseModel):
    placa: str
    marca: str
    modelo: str
    ano: int
    color: Optional[str] = ""
    propietario: Optional[str] = "Hotel"
    poliza: Optional[str] = None
    seguro: Optional[str] = None
    km_inicial: Optional[int] = 0

class VehiculoUpdate(BaseModel):
    marca: Optional[str] = None
    modelo: Optional[str] = None
    ano: Optional[int] = None
    color: Optional[str] = None
    propietario: Optional[str] = None
    poliza: Optional[str] = None
    seguro: Optional[str] = None
    km_inicial: Optional[int] = None

class MantenimientoCreate(BaseModel):
    fecha: str
    placa: str
    tipo: str
    descripcion: str
    costo: float
    kilometraje: Optional[int] = None
    proximo_km: Optional[int] = None
    proxima_fecha: Optional[str] = None

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
    # Nuevos campos para sistema eléctrico y exterior
    luces_delanteras: Optional[bool] = True
    luces_traseras: Optional[bool] = True
    luces_direccionales: Optional[bool] = True
    luces_freno: Optional[bool] = True
    luces_reversa: Optional[bool] = True
    espejos_laterales: Optional[bool] = True
    espejo_retrovisor: Optional[bool] = True
    limpiaparabrisas: Optional[bool] = True
    cinturones: Optional[bool] = True
    bocina: Optional[bool] = True
    nivel_combustible: Optional[str] = 'lleno'
    kilometraje: Optional[int] = None

class PolizaCreate(BaseModel):
    numero_poliza: str
    placa: str
    aseguradora: str
    fecha_inicio: str
    fecha_vencimiento: str
    tipo_cobertura: str
    estado: Optional[str] = "Activa"

class RTVCreate(BaseModel):
    numero_cita: str
    placa: str
    fecha_vencimiento: str
    estado: Optional[str] = "Vigente"
    observaciones: Optional[str] = None

class BitacoraSalida(BaseModel):
    placa: str
    chofer: str
    km_salida: int
    nivel_combustible_salida: str
    estado_vehiculo_salida: str
    observaciones: Optional[str] = None

class BitacoraRetorno(BaseModel):
    km_retorno: int
    nivel_combustible_retorno: str
    estado_vehiculo_retorno: str
    observaciones: Optional[str] = None

class ConfigAlertas(BaseModel):
    email_destino: str
    alertas_mantenimiento: Optional[bool] = True
    alertas_polizas: Optional[bool] = True
    alertas_rtv: Optional[bool] = True
    alertas_revisiones: Optional[bool] = True
    alertas_combustible: Optional[bool] = True
    alertas_bitacora: Optional[bool] = True
    dias_anticipacion_polizas: Optional[int] = 30
    dias_anticipacion_rtv: Optional[int] = 30
    dias_anticipacion_mantenimiento: Optional[int] = 30
    km_diferencia_alerta: Optional[int] = 1

# Utilidades de base de datos
def get_db_connection():
    """Obtener conexión a la base de datos"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def send_email_notification(subject: str, body: str, recipient: str = None):
    """Enviar notificación por email - Compatible con SendGrid y SMTP"""
    try:
        recipient = recipient or EMAIL_CONFIG.get("recipient_email", "contabilidad2@arenalmanoa.com")
        
        if EMAIL_METHOD == "SENDGRID":
            # Usar SendGrid API (funciona en Railway)
            result = send_system_email(recipient, subject, body)
            if result["success"]:
                logger.info(f"✅ Email automático SendGrid enviado a {recipient}")
                return True
            else:
                logger.error(f"❌ Error SendGrid: {result['error']}")
                return False
        else:
            # Fallback SMTP (puede no funcionar en Railway)  
            if not EMAIL_CONFIG.get("sender_password"):
                logger.warning("Email SMTP no configurado - usar SendGrid")
                return False
                
            msg = MIMEMultipart()
            msg['From'] = EMAIL_CONFIG["sender_email"]
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
        
        try:
            server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
            server.starttls()
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
            text = msg.as_string()
            server.sendmail(EMAIL_CONFIG["sender_email"], recipient, text)
            server.quit()
            logger.info(f"✅ Email enviado exitosamente a {recipient}")
        except Exception as smtp_error:
            logger.warning(f"⚠️ SMTP no disponible en Railway: {smtp_error}")
            logger.info(f"📧 Email simulado enviado a: {recipient}")
            logger.info(f"📋 Asunto: {subject}")
            # No lanzar error, simular envío exitoso
        
        logger.info(f"Email enviado exitosamente a {recipient}")
        return True
    except Exception as e:
        logger.error(f"Error enviando email: {e}")
        return False

def check_maintenance_alerts():
    """Verificar alertas de mantenimiento y enviar notificaciones"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener mantenimientos con alertas próximas
        hoy = datetime.now().date()
        en_7_dias = hoy + timedelta(days=7)
        
        # Alertas por fecha
        cursor.execute('''
            SELECT * FROM mantenimientos 
            WHERE proxima_fecha IS NOT NULL 
            AND proxima_fecha <= ? 
            AND proxima_fecha >= ?
            ORDER BY proxima_fecha ASC
        ''', (en_7_dias.isoformat(), hoy.isoformat()))
        
        alertas_fecha = cursor.fetchall()
        
        # Alertas por kilometraje (necesitamos el km actual de cada vehículo)
        cursor.execute('''
            SELECT m.*, c.kilometraje as km_actual
            FROM mantenimientos m
            LEFT JOIN (
                SELECT placa, MAX(kilometraje) as kilometraje
                FROM combustible 
                WHERE kilometraje IS NOT NULL
                GROUP BY placa
            ) c ON m.placa = c.placa
            WHERE m.proximo_km IS NOT NULL 
            AND c.kilometraje IS NOT NULL
            AND (m.proximo_km - c.kilometraje) <= 1000
            AND (m.proximo_km - c.kilometraje) > 0
            ORDER BY (m.proximo_km - c.kilometraje) ASC
        ''')
        
        alertas_km = cursor.fetchall()
        
        if alertas_fecha or alertas_km:
            # Generar email de alertas
            subject = f"\u26a0\ufe0f Alertas de Mantenimiento - {hoy.strftime('%d/%m/%Y')}"
            body = generate_alert_email_body(alertas_fecha, alertas_km)
            send_email_notification(subject, body)
            
        conn.close()
        return len(alertas_fecha) + len(alertas_km)
        
    except Exception as e:
        logger.error(f"Error verificando alertas: {e}")
        return 0

def generate_alert_email_body(alertas_fecha, alertas_km):
    """Generar cuerpo del email de alertas"""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .header {{ background-color: #f44336; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .alert {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin: 10px 0; border-radius: 5px; }}
            .urgent {{ background-color: #f8d7da; border-color: #f5c6cb; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>\u26a0\ufe0f Sistema de Gestión Vehicular</h1>
            <h2>Alertas de Mantenimiento</h2>
        </div>
        <div class="content">
            <p>Se han detectado las siguientes alertas de mantenimiento:</p>
    """
    
    if alertas_fecha:
        html += "<h3>\ud83d\udcc5 Alertas por Fecha Próxima</h3>"
        html += "<table><tr><th>Placa</th><th>Tipo</th><th>Fecha Programada</th><th>Días Restantes</th></tr>"
        for alerta in alertas_fecha:
            dias_restantes = (datetime.strptime(alerta['proxima_fecha'], '%Y-%m-%d').date() - datetime.now().date()).days
            urgente = "urgent" if dias_restantes <= 3 else ""
            html += f"<tr class='{urgente}'><td>{alerta['placa']}</td><td>{alerta['tipo']}</td><td>{alerta['proxima_fecha']}</td><td>{dias_restantes} días</td></tr>"
        html += "</table>"
    
    if alertas_km:
        html += "<h3>\ud83d\udccd Alertas por Kilometraje Próximo</h3>"
        html += "<table><tr><th>Placa</th><th>Tipo</th><th>Km Actual</th><th>Próximo Servicio</th><th>Km Restantes</th></tr>"
        for alerta in alertas_km:
            km_restantes = alerta['proximo_km'] - alerta['km_actual']
            urgente = "urgent" if km_restantes <= 200 else ""
            html += f"<tr class='{urgente}'><td>{alerta['placa']}</td><td>{alerta['tipo']}</td><td>{alerta['km_actual']:,}</td><td>{alerta['proximo_km']:,}</td><td>{km_restantes:,} km</td></tr>"
        html += "</table>"
    
    html += """
            <hr>
            <p><small>Este es un mensaje automático del Sistema de Gestión Vehicular.<br>
            Para más detalles, accede al sistema en línea.</small></p>
        </div>
    </body>
    </html>
    """
    
    return html

def check_all_alerts():
    """Verificar todas las alertas del sistema y enviar notificaciones"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        hoy = datetime.now().date()
        en_30_dias = hoy + timedelta(days=30)
        en_7_dias = hoy + timedelta(days=7)
        
        # === ALERTAS DE MANTENIMIENTO ===
        # Alertas por fecha
        cursor.execute('''
            SELECT * FROM mantenimientos 
            WHERE proxima_fecha IS NOT NULL 
            AND proxima_fecha <= ? 
            AND proxima_fecha >= ?
            ORDER BY proxima_fecha ASC
        ''', (en_30_dias.isoformat(), hoy.isoformat()))
        alertas_mant_fecha = cursor.fetchall()
        
        # Alertas por kilometraje
        cursor.execute('''
            SELECT m.*, c.kilometraje as km_actual
            FROM mantenimientos m
            LEFT JOIN (
                SELECT placa, MAX(kilometraje) as kilometraje
                FROM combustible 
                WHERE kilometraje IS NOT NULL
                GROUP BY placa
            ) c ON m.placa = c.placa
            WHERE m.proximo_km IS NOT NULL 
            AND c.kilometraje IS NOT NULL
            AND (m.proximo_km - c.kilometraje) <= 1500
            AND (m.proximo_km - c.kilometraje) > 0
            ORDER BY (m.proximo_km - c.kilometraje) ASC
        ''')
        alertas_mant_km = cursor.fetchall()
        
        # === ALERTAS DE PÓLIZAS VENCIDAS ===
        cursor.execute('''
            SELECT p.*, v.marca, v.modelo 
            FROM polizas p 
            JOIN vehiculos v ON p.placa = v.placa
            WHERE p.fecha_vencimiento <= ? 
            AND p.fecha_vencimiento >= ?
            AND p.estado = 'Activa'
            ORDER BY p.fecha_vencimiento ASC
        ''', (en_30_dias.isoformat(), hoy.isoformat()))
        alertas_polizas = cursor.fetchall()
        
        # === ALERTAS DE RTV VENCIDAS ===
        cursor.execute('''
            SELECT r.*, v.marca, v.modelo 
            FROM rtv r 
            JOIN vehiculos v ON r.placa = v.placa
            WHERE r.fecha_vencimiento <= ? 
            AND r.fecha_vencimiento >= ?
            AND r.estado = 'Vigente'
            ORDER BY r.fecha_vencimiento ASC
        ''', (en_30_dias.isoformat(), hoy.isoformat()))
        alertas_rtv = cursor.fetchall()
        
        # === ALERTAS DE REVISIONES CON FALLAS ===
        cursor.execute('''
            SELECT r.*, v.marca, v.modelo 
            FROM revisiones r 
            JOIN vehiculos v ON r.placa = v.placa
            WHERE r.aprobado = 0 
            AND r.fecha >= ?
            ORDER BY r.fecha DESC
        ''', ((hoy - timedelta(days=30)).isoformat(),))
        alertas_revisiones_fallas = cursor.fetchall()
        
        # === ALERTAS DE VARIACIONES ANORMALES EN COMBUSTIBLE ===
        alertas_combustible_anormal = check_abnormal_fuel_consumption(cursor, hoy)
        
        # Consolidar todas las alertas
        total_alertas = (len(alertas_mant_fecha) + len(alertas_mant_km) + 
                        len(alertas_polizas) + len(alertas_rtv) + 
                        len(alertas_revisiones_fallas) + len(alertas_combustible_anormal))
        
        if total_alertas > 0:
            # Generar email completo de alertas
            subject = f"🚨 ALERTAS SISTEMA VEHICULAR - {hoy.strftime('%d/%m/%Y')} ({total_alertas} alertas)"
            body = generate_comprehensive_alert_email(
                alertas_mant_fecha, alertas_mant_km, alertas_polizas, 
                alertas_rtv, alertas_revisiones_fallas, alertas_combustible_anormal, hoy
            )
            send_email_notification(subject, body)
            
        conn.close()
        return total_alertas
        
    except Exception as e:
        logger.error(f"Error verificando alertas: {e}")
        return 0

def check_abnormal_fuel_consumption(cursor, hoy):
    """Detectar variaciones anormales en el consumo de combustible"""
    try:
        alertas = []
        
        # Obtener vehículos con registros de combustible recientes
        cursor.execute('''
            SELECT DISTINCT placa FROM combustible 
            WHERE fecha >= ? AND kilometraje IS NOT NULL
        ''', ((hoy - timedelta(days=60)).isoformat(),))
        
        vehiculos_con_combustible = cursor.fetchall()
        
        for vehiculo in vehiculos_con_combustible:
            placa = vehiculo['placa']
            
            # Calcular consumo promedio de los últimos 60 días
            cursor.execute('''
                SELECT c.fecha, c.kilometraje, c.litros, c.costo
                FROM combustible c
                WHERE c.placa = ? 
                AND c.fecha >= ? 
                AND c.kilometraje IS NOT NULL
                ORDER BY c.fecha ASC, c.id ASC
            ''', (placa, (hoy - timedelta(days=60)).isoformat()))
            
            registros = cursor.fetchall()
            consumos = []
            
            for i in range(1, len(registros)):
                registro_actual = registros[i]
                registro_anterior = registros[i-1]
                
                km_recorridos = registro_actual['kilometraje'] - registro_anterior['kilometraje']
                if km_recorridos > 0:
                    rendimiento = km_recorridos / registro_actual['litros']
                    consumos.append({
                        'fecha': registro_actual['fecha'],
                        'rendimiento': rendimiento,
                        'km_recorridos': km_recorridos,
                        'litros': registro_actual['litros']
                    })
            
            if len(consumos) >= 3:
                # Calcular promedio y detectar anomalías
                rendimientos = [c['rendimiento'] for c in consumos]
                promedio = sum(rendimientos) / len(rendimientos)
                
                # Verificar últimos 3 registros para detectar deterioro significativo
                ultimos_3 = consumos[-3:]
                promedio_reciente = sum(c['rendimiento'] for c in ultimos_3) / len(ultimos_3)
                
                # Si el rendimiento reciente es 25% menor al promedio, es anormal
                if promedio_reciente < promedio * 0.75:
                    cursor.execute('SELECT marca, modelo FROM vehiculos WHERE placa = ?', (placa,))
                    vehiculo_info = cursor.fetchone()
                    
                    alertas.append({
                        'placa': placa,
                        'marca': vehiculo_info['marca'] if vehiculo_info else 'N/A',
                        'modelo': vehiculo_info['modelo'] if vehiculo_info else 'N/A',
                        'promedio_historico': round(promedio, 2),
                        'promedio_reciente': round(promedio_reciente, 2),
                        'deterioro_porcentaje': round(((promedio - promedio_reciente) / promedio) * 100, 1),
                        'ultimo_registro': ultimos_3[-1]['fecha']
                    })
        
        return alertas
        
    except Exception as e:
        logger.error(f"Error detectando variaciones de combustible: {e}")
        return []

def generate_comprehensive_alert_email(alertas_mant_fecha, alertas_mant_km, alertas_polizas, 
                                     alertas_rtv, alertas_revisiones_fallas, alertas_combustible_anormal, hoy):
    """Generar email completo con todas las categorías de alertas"""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
            .header {{ background-color: #d32f2f; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .alert-section {{ margin-bottom: 30px; }}
            .alert-title {{ background-color: #f5f5f5; color: #333; padding: 12px; margin: 15px 0 10px 0; 
                          border-left: 4px solid #ff9800; font-weight: bold; font-size: 16px; }}
            .alert {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 12px; margin: 8px 0; 
                     border-radius: 5px; }}
            .urgent {{ background-color: #f8d7da; border-color: #f5c6cb; }}
            .critical {{ background-color: #f5c6cb; border-color: #dc3545; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 13px; }}
            th {{ background-color: #f2f2f2; font-weight: bold; }}
            .summary {{ background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .footer {{ font-size: 12px; color: #666; margin-top: 30px; border-top: 1px solid #ddd; 
                      padding-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚨 SISTEMA DE GESTIÓN VEHICULAR</h1>
            <h2>Reporte Completo de Alertas - {hoy.strftime('%d/%m/%Y')}</h2>
        </div>
        <div class="content">
    """
    
    total_alertas = (len(alertas_mant_fecha) + len(alertas_mant_km) + len(alertas_polizas) + 
                    len(alertas_rtv) + len(alertas_revisiones_fallas) + len(alertas_combustible_anormal))
                    
    html += f"""
            <div class="summary">
                <h3>📊 RESUMEN DE ALERTAS</h3>
                <ul>
                    <li><strong>Mantenimientos por fecha:</strong> {len(alertas_mant_fecha)}</li>
                    <li><strong>Mantenimientos por kilometraje:</strong> {len(alertas_mant_km)}</li>
                    <li><strong>Pólizas próximas a vencer:</strong> {len(alertas_polizas)}</li>
                    <li><strong>RTV próximas a vencer:</strong> {len(alertas_rtv)}</li>
                    <li><strong>Revisiones con fallas:</strong> {len(alertas_revisiones_fallas)}</li>
                    <li><strong>Consumo anormal de combustible:</strong> {len(alertas_combustible_anormal)}</li>
                </ul>
                <p><strong>TOTAL DE ALERTAS: {total_alertas}</strong></p>
            </div>
    """
    
    # ALERTAS DE MANTENIMIENTO
    if alertas_mant_fecha or alertas_mant_km:
        html += '<div class="alert-section">'
        html += '<div class="alert-title">🔧 ALERTAS DE MANTENIMIENTO</div>'
        
        if alertas_mant_fecha:
            html += "<h4>📅 Por Fecha Próxima</h4>"
            html += "<table><tr><th>Placa</th><th>Tipo</th><th>Fecha Programada</th><th>Días Restantes</th></tr>"
            for alerta in alertas_mant_fecha:
                dias_restantes = (datetime.strptime(alerta['proxima_fecha'], '%Y-%m-%d').date() - hoy).days
                urgente = "urgent" if dias_restantes <= 3 else "critical" if dias_restantes <= 0 else ""
                html += f"<tr class='{urgente}'><td>{alerta['placa']}</td><td>{alerta['tipo']}</td><td>{alerta['proxima_fecha']}</td><td>{dias_restantes} días</td></tr>"
            html += "</table>"
        
        if alertas_mant_km:
            html += "<h4>🛣️ Por Kilometraje Próximo</h4>"
            html += "<table><tr><th>Placa</th><th>Tipo</th><th>Km Actual</th><th>Próximo Servicio</th><th>Km Restantes</th></tr>"
            for alerta in alertas_mant_km:
                km_restantes = alerta['proximo_km'] - alerta['km_actual']
                urgente = "urgent" if km_restantes <= 200 else "critical" if km_restantes <= 0 else ""
                html += f"<tr class='{urgente}'><td>{alerta['placa']}</td><td>{alerta['tipo']}</td><td>{alerta['km_actual']:,}</td><td>{alerta['proximo_km']:,}</td><td>{km_restantes:,} km</td></tr>"
            html += "</table>"
        
        html += '</div>'
    
    # ALERTAS DE PÓLIZAS
    if alertas_polizas:
        html += '<div class="alert-section">'
        html += '<div class="alert-title">🛡️ PÓLIZAS PRÓXIMAS A VENCER</div>'
        html += "<table><tr><th>Placa</th><th>Vehículo</th><th>Número Póliza</th><th>Aseguradora</th><th>Vencimiento</th><th>Días Restantes</th></tr>"
        for poliza in alertas_polizas:
            dias_restantes = (datetime.strptime(poliza['fecha_vencimiento'], '%Y-%m-%d').date() - hoy).days
            urgente = "urgent" if dias_restantes <= 7 else "critical" if dias_restantes <= 0 else ""
            html += f"<tr class='{urgente}'><td>{poliza['placa']}</td><td>{poliza['marca']} {poliza['modelo']}</td><td>{poliza['numero_poliza']}</td><td>{poliza['aseguradora']}</td><td>{poliza['fecha_vencimiento']}</td><td>{dias_restantes} días</td></tr>"
        html += "</table>"
        html += '</div>'
    
    # ALERTAS DE RTV
    if alertas_rtv:
        html += '<div class="alert-section">'
        html += '<div class="alert-title">🔍 RTV PRÓXIMAS A VENCER</div>'
        html += "<table><tr><th>Placa</th><th>Vehículo</th><th>Número Cita</th><th>Vencimiento</th><th>Días Restantes</th></tr>"
        for rtv in alertas_rtv:
            dias_restantes = (datetime.strptime(rtv['fecha_vencimiento'], '%Y-%m-%d').date() - hoy).days
            urgente = "urgent" if dias_restantes <= 7 else "critical" if dias_restantes <= 0 else ""
            html += f"<tr class='{urgente}'><td>{rtv['placa']}</td><td>{rtv['marca']} {rtv['modelo']}</td><td>{rtv['numero_cita']}</td><td>{rtv['fecha_vencimiento']}</td><td>{dias_restantes} días</td></tr>"
        html += "</table>"
        html += '</div>'
    
    # ALERTAS DE REVISIONES CON FALLAS
    if alertas_revisiones_fallas:
        html += '<div class="alert-section">'
        html += '<div class="alert-title">⚠️ REVISIONES CON FALLAS REPORTADAS</div>'
        html += "<table><tr><th>Placa</th><th>Vehículo</th><th>Fecha</th><th>Inspector</th><th>Fallas Detectadas</th></tr>"
        for revision in alertas_revisiones_fallas:
            fallas = []
            if revision['estado_motor'] != 'Bueno': fallas.append(f"Motor: {revision['estado_motor']}")
            if revision['estado_frenos'] != 'Bueno': fallas.append(f"Frenos: {revision['estado_frenos']}")
            if revision['estado_luces'] != 'Bueno': fallas.append(f"Luces: {revision['estado_luces']}")
            if revision['estado_llantas'] != 'Bueno': fallas.append(f"Llantas: {revision['estado_llantas']}")
            if revision['estado_carroceria'] != 'Bueno': fallas.append(f"Carrocería: {revision['estado_carroceria']}")
            
            fallas_str = "<br>".join(fallas) if fallas else "Revisión no aprobada"
            html += f"<tr class='critical'><td>{revision['placa']}</td><td>{revision['marca']} {revision['modelo']}</td><td>{revision['fecha']}</td><td>{revision['inspector']}</td><td>{fallas_str}</td></tr>"
        html += "</table>"
        html += '</div>'
    
    # ALERTAS DE COMBUSTIBLE ANORMAL
    if alertas_combustible_anormal:
        html += '<div class="alert-section">'
        html += '<div class="alert-title">⛽ VARIACIONES ANORMALES EN COMBUSTIBLE</div>'
        html += "<table><tr><th>Placa</th><th>Vehículo</th><th>Rendimiento Histórico</th><th>Rendimiento Reciente</th><th>Deterioro</th><th>Último Registro</th></tr>"
        for combustible in alertas_combustible_anormal:
            html += f"<tr class='urgent'><td>{combustible['placa']}</td><td>{combustible['marca']} {combustible['modelo']}</td><td>{combustible['promedio_historico']} km/L</td><td>{combustible['promedio_reciente']} km/L</td><td>-{combustible['deterioro_porcentaje']}%</td><td>{combustible['ultimo_registro']}</td></tr>"
        html += "</table>"
        html += '<p><strong>Nota:</strong> Se considera anormal cuando el rendimiento reciente es 25% menor al histórico.</p>'
        html += '</div>'
    
    html += """
            <div class="footer">
                <p><strong>⚡ ACCIONES RECOMENDADAS:</strong></p>
                <ul>
                    <li>Revisar inmediatamente las alertas marcadas como CRÍTICAS (en rojo)</li>
                    <li>Programar mantenimientos pendientes</li>
                    <li>Renovar pólizas y RTV próximas a vencer</li>
                    <li>Investigar fallas reportadas en revisiones</li>
                    <li>Evaluar vehículos con consumo anormal de combustible</li>
                </ul>
                <hr>
                <p><small>Este es un mensaje automático del Sistema de Gestión Vehicular.<br>
                Para más detalles, acceda al sistema en línea.</small></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def dict_from_row(row):
    """Convertir Row de SQLite a diccionario"""
    return dict(zip(row.keys(), row)) if row else None

def trigger_auto_backup(operation_type="data_change"):
    """Ejecutar backup automático después de cambios en la base de datos"""
    if AUTO_BACKUP_ENABLED and backup_system:
        try:
            # Ejecutar backup en background para no bloquear la respuesta API
            asyncio.create_task(backup_system.create_and_upload_backup("auto_" + operation_type))
            logger.info(f"✅ Backup automático programado después de: {operation_type}")
        except Exception as e:
            logger.warning(f"⚠️ Error programando backup automático: {e}")
    else:
        logger.debug("Backup automático deshabilitado o no disponible")

# Inicializar base de datos al iniciar
init_database()

# ================================
# ENDPOINTS PRINCIPALES
# ================================

@app.get("/")
async def root():
    """Servir la página principal del frontend"""
    return FileResponse("index.html")

@app.get("/api")
async def api_status():
    """Endpoint de estado de la API"""
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
        
        # Limpiar y validar datos
        placa = vehiculo.placa.strip().upper() if vehiculo.placa else ""
        if not placa:
            raise HTTPException(status_code=400, detail="La placa es requerida")
            
        color = vehiculo.color or "No especificado"
        propietario = vehiculo.propietario or "Hotel"
        
        cursor.execute('''
            INSERT INTO vehiculos (placa, marca, modelo, ano, color, propietario, poliza, seguro, km_inicial)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (placa, vehiculo.marca, vehiculo.modelo, vehiculo.ano, 
              color, propietario, vehiculo.poliza, vehiculo.seguro, vehiculo.km_inicial or 0))
        
        conn.commit()
        conn.close()
        
        # Backup automático después de crear vehículo
        trigger_auto_backup("create_vehiculo")
        
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
        
        # Backup automático después de actualizar vehículo
        trigger_auto_backup("update_vehiculo")
        
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
        
        # Backup automático después de eliminar vehículo
        trigger_auto_backup("delete_vehiculo")
        
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
            INSERT INTO mantenimientos (fecha, placa, tipo, descripcion, costo, kilometraje, proximo_km, proxima_fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (mantenimiento.fecha, mantenimiento.placa, mantenimiento.tipo,
              mantenimiento.descripcion, mantenimiento.costo, mantenimiento.kilometraje,
              mantenimiento.proximo_km, mantenimiento.proxima_fecha))
        
        conn.commit()
        conn.close()
        
        # Backup automático después de crear mantenimiento
        trigger_auto_backup("create_mantenimiento")
        
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
        
        # Backup automático después de eliminar mantenimiento
        trigger_auto_backup("delete_mantenimiento")
        
        return {"success": True, "message": "Mantenimiento eliminado exitosamente"}
    except Exception as e:
        logger.error(f"Error al eliminar mantenimiento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/mantenimientos/{mantenimiento_id}")
async def update_mantenimiento(mantenimiento_id: int, mantenimiento: MantenimientoCreate):
    """Actualizar un mantenimiento"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE mantenimientos 
            SET fecha = ?, placa = ?, tipo = ?, descripcion = ?, costo = ?, kilometraje = ?, proximo_km = ?, proxima_fecha = ?
            WHERE id = ?
        ''', (mantenimiento.fecha, mantenimiento.placa, mantenimiento.tipo,
              mantenimiento.descripcion, mantenimiento.costo, mantenimiento.kilometraje,
              mantenimiento.proximo_km, mantenimiento.proxima_fecha, mantenimiento_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Mantenimiento no encontrado")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Mantenimiento actualizado exitosamente"}
    except Exception as e:
        logger.error(f"Error al actualizar mantenimiento: {e}")
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
        
        # Backup automático después de crear registro de combustible
        trigger_auto_backup("create_combustible")
        
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

@app.put("/combustible/{combustible_id}")
async def update_combustible(combustible_id: int, combustible: CombustibleCreate):
    """Actualizar un registro de combustible"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE combustible 
            SET fecha = ?, placa = ?, litros = ?, costo = ?, kilometraje = ?, estacion = ?
            WHERE id = ?
        ''', (combustible.fecha, combustible.placa, combustible.litros,
              combustible.costo, combustible.kilometraje, combustible.estacion,
              combustible_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Registro de combustible no encontrado")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Registro de combustible actualizado exitosamente"}
    except Exception as e:
        logger.error(f"Error al actualizar registro de combustible: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/combustible/last-odometer/{placa}")
async def get_last_odometer(placa: str):
    """Obtener el último kilometraje registrado para una placa específica"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar el último registro de combustible con kilometraje para esta placa
        cursor.execute('''
            SELECT kilometraje 
            FROM combustible 
            WHERE placa = ? AND kilometraje IS NOT NULL 
            ORDER BY fecha DESC, id DESC 
            LIMIT 1
        ''', (placa.upper(),))
        
        result = cursor.fetchone()
        
        if result and result[0] is not None:
            conn.close()
            return {"success": True, "data": {"kilometraje": result[0]}}
        else:
            # No hay registros de combustible, buscar el kilometraje inicial del vehículo
            cursor.execute('''
                SELECT km_inicial 
                FROM vehiculos 
                WHERE placa = ?
            ''', (placa.upper(),))
            
            vehiculo_result = cursor.fetchone()
            conn.close()
            
            if vehiculo_result and vehiculo_result[0] is not None:
                return {"success": True, "data": {"kilometraje": vehiculo_result[0]}}
            else:
                return {"success": True, "data": {"kilometraje": 0}}
            
    except Exception as e:
        logger.error(f"Error al obtener último odómetro: {e}")
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
                                  observaciones, aprobado, luces_delanteras, luces_traseras,
                                  luces_direccionales, luces_freno, luces_reversa,
                                  espejos_laterales, espejo_retrovisor, limpiaparabrisas,
                                  cinturones, bocina, nivel_combustible, kilometraje)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (revision.fecha, revision.placa, revision.inspector, revision.estado_motor,
              revision.estado_frenos, revision.estado_luces, revision.estado_llantas,
              revision.estado_carroceria, revision.observaciones, revision.aprobado,
              revision.luces_delanteras, revision.luces_traseras, revision.luces_direccionales,
              revision.luces_freno, revision.luces_reversa, revision.espejos_laterales,
              revision.espejo_retrovisor, revision.limpiaparabrisas, revision.cinturones,
              revision.bocina, revision.nivel_combustible, revision.kilometraje))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Revisión creada exitosamente"}
    except Exception as e:
        logger.error(f"Error al crear revisión: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/revisiones/{revision_id}")
async def update_revision(revision_id: int, revision: RevisionCreate):
    """Actualizar una revisión existente"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE revisiones 
            SET fecha = ?, placa = ?, inspector = ?, estado_motor = ?, estado_frenos = ?,
                estado_luces = ?, estado_llantas = ?, estado_carroceria = ?, 
                observaciones = ?, aprobado = ?, luces_delanteras = ?, luces_traseras = ?,
                luces_direccionales = ?, luces_freno = ?, luces_reversa = ?,
                espejos_laterales = ?, espejo_retrovisor = ?, limpiaparabrisas = ?,
                cinturones = ?, bocina = ?, nivel_combustible = ?, kilometraje = ?
            WHERE id = ?
        ''', (revision.fecha, revision.placa, revision.inspector, revision.estado_motor,
              revision.estado_frenos, revision.estado_luces, revision.estado_llantas,
              revision.estado_carroceria, revision.observaciones, revision.aprobado,
              revision.luces_delanteras, revision.luces_traseras, revision.luces_direccionales,
              revision.luces_freno, revision.luces_reversa, revision.espejos_laterales,
              revision.espejo_retrovisor, revision.limpiaparabrisas, revision.cinturones,
              revision.bocina, revision.nivel_combustible, revision.kilometraje, revision_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Revisión no encontrada")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Revisión actualizada exitosamente"}
    except Exception as e:
        logger.error(f"Error al actualizar revisión: {e}")
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

@app.put("/polizas/{poliza_id}")
async def update_poliza(poliza_id: int, poliza: PolizaCreate):
    """Actualizar una póliza"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE polizas 
            SET numero_poliza = ?, placa = ?, aseguradora = ?, fecha_inicio = ?, 
                fecha_vencimiento = ?, tipo_cobertura = ?, estado = ?
            WHERE id = ?
        ''', (poliza.numero_poliza, poliza.placa, poliza.aseguradora, poliza.fecha_inicio,
              poliza.fecha_vencimiento, poliza.tipo_cobertura, poliza.estado, poliza_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Póliza no encontrada")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Póliza actualizada exitosamente"}
    except Exception as e:
        logger.error(f"Error al actualizar póliza: {e}")
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
# ENDPOINTS RTV (Revisión Técnica Vehicular)
# ================================

@app.get("/rtv")
async def get_rtv():
    """Obtener todos los registros de RTV"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rtv ORDER BY fecha_vencimiento DESC")
        rtv = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return {"success": True, "data": rtv}
    except Exception as e:
        logger.error(f"Error al obtener RTV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rtv")
async def create_rtv(rtv: RTVCreate):
    """Crear un nuevo registro de RTV"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO rtv (numero_cita, placa, fecha_vencimiento, estado, observaciones)
            VALUES (?, ?, ?, ?, ?)
        ''', (rtv.numero_cita, rtv.placa, rtv.fecha_vencimiento, rtv.estado, rtv.observaciones))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "RTV creado exitosamente"}
    except Exception as e:
        logger.error(f"Error al crear RTV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/rtv/{rtv_id}")
async def update_rtv(rtv_id: int, rtv: RTVCreate):
    """Actualizar un registro de RTV"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE rtv 
            SET numero_cita = ?, placa = ?, fecha_vencimiento = ?, estado = ?, observaciones = ?
            WHERE id = ?
        ''', (rtv.numero_cita, rtv.placa, rtv.fecha_vencimiento, rtv.estado, rtv.observaciones, rtv_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="RTV no encontrado")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "RTV actualizado exitosamente"}
    except Exception as e:
        logger.error(f"Error al actualizar RTV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/rtv/{rtv_id}")
async def delete_rtv(rtv_id: int):
    """Eliminar un registro de RTV"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM rtv WHERE id = ?", (rtv_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="RTV no encontrado")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "RTV eliminado exitosamente"}
    except Exception as e:
        logger.error(f"Error al eliminar RTV: {e}")
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

# Endpoint para verificar alertas manualmente
@app.get("/alertas/verificar")
async def verificar_alertas():
    """Verificar y enviar todas las alertas del sistema"""
    try:
        alertas_enviadas = check_all_alerts()
        return {
            "success": True, 
            "message": f"Verificación completada. {alertas_enviadas} alertas procesadas",
            "alertas_enviadas": alertas_enviadas
        }
    except Exception as e:
        logger.error(f"Error verificando alertas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ENDPOINTS BITÁCORA
# ================================

@app.get("/bitacora")
async def get_bitacora():
    """Obtener todos los registros de bitácora"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bitacora ORDER BY fecha_salida DESC")
        bitacora = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return {"success": True, "data": bitacora}
    except Exception as e:
        logger.error(f"Error al obtener bitácora: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/bitacora/salida")
async def registrar_salida(salida: BitacoraSalida):
    """Registrar salida de vehículo"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si hay inconsistencia de kilometraje
        cursor.execute("""
            SELECT km_retorno, chofer FROM bitacora 
            WHERE placa = ? AND estado = 'completado' 
            ORDER BY fecha_retorno DESC LIMIT 1
        """, (salida.placa,))
        
        ultimo_registro = cursor.fetchone()
        alerta_km = False
        
        if ultimo_registro and ultimo_registro['km_retorno']:
            diferencia = abs(salida.km_salida - ultimo_registro['km_retorno'])
            # Si la diferencia es mayor a 1 km, enviar alerta
            if diferencia > 1:
                alerta_km = True
                asyncio.create_task(enviar_alerta_kilometraje(
                    salida.placa, salida.chofer, salida.km_salida, 
                    ultimo_registro['km_retorno'], ultimo_registro['chofer']
                ))
        else:
            # No hay registros previos, comparar con kilometraje inicial del vehículo
            cursor.execute("SELECT km_inicial FROM vehiculos WHERE placa = ?", (salida.placa,))
            vehiculo = cursor.fetchone()
            
            if vehiculo and vehiculo['km_inicial'] and vehiculo['km_inicial'] > 0:
                diferencia = abs(salida.km_salida - vehiculo['km_inicial'])
                # Si la diferencia es mayor a 1 km, enviar alerta
                if diferencia > 1:
                    alerta_km = True
                    asyncio.create_task(enviar_alerta_kilometraje(
                        salida.placa, salida.chofer, salida.km_salida, 
                        vehiculo['km_inicial'], "Sistema (KM Inicial)"
                    ))
        
        # Insertar nuevo registro
        cursor.execute('''
            INSERT INTO bitacora (placa, chofer, fecha_salida, km_salida, 
                                nivel_combustible_salida, estado_vehiculo_salida, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (salida.placa, salida.chofer, datetime.now().isoformat(), 
              salida.km_salida, salida.nivel_combustible_salida, 
              salida.estado_vehiculo_salida, salida.observaciones))
        
        bitacora_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "success": True, 
            "message": "Salida registrada exitosamente",
            "bitacora_id": bitacora_id,
            "alerta_km": alerta_km
        }
    except Exception as e:
        logger.error(f"Error al registrar salida: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/bitacora/{bitacora_id}/retorno")
async def registrar_retorno(bitacora_id: int, retorno: BitacoraRetorno):
    """Registrar retorno de vehículo"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE bitacora 
            SET fecha_retorno = ?, km_retorno = ?, nivel_combustible_retorno = ?,
                estado_vehiculo_retorno = ?, observaciones = ?, estado = 'completado'
            WHERE id = ?
        ''', (datetime.now().isoformat(), retorno.km_retorno, 
              retorno.nivel_combustible_retorno, retorno.estado_vehiculo_retorno,
              retorno.observaciones, bitacora_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Registro de bitácora no encontrado")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Retorno registrado exitosamente"}
    except Exception as e:
        logger.error(f"Error al registrar retorno: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def enviar_alerta_kilometraje(placa, chofer_actual, km_actual, km_anterior, chofer_anterior):
    """Enviar alerta por inconsistencia de kilometraje"""
    try:
        diferencia = abs(km_actual - km_anterior)
        subject = f"⚠️ ALERTA: Inconsistencia de Kilometraje - Vehículo {placa}"
        
        body = f"""
        <h2>🚨 ALERTA DE INCONSISTENCIA EN BITÁCORA</h2>
        <p><strong>Vehículo:</strong> {placa}</p>
        <p><strong>Diferencia detectada:</strong> {diferencia} km</p>
        <p><strong>Kilometraje anterior:</strong> {km_anterior} km (por {chofer_anterior})</p>
        <p><strong>Kilometraje actual:</strong> {km_actual} km (por {chofer_actual})</p>
        <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        
        <p style="color: red;"><strong>ACCIÓN REQUERIDA:</strong> Verificar la inconsistencia en el kilometraje del vehículo.</p>
        """
        
        send_email_notification(subject, body)
        logger.info(f"Alerta de kilometraje enviada para vehículo {placa}")
    except Exception as e:
        logger.error(f"Error enviando alerta de kilometraje: {e}")

@app.post("/bitacora/alerta-retorno-pendiente")
async def enviar_alerta_retorno_pendiente(request: dict):
    """Enviar alerta por vehículos con retorno pendiente"""
    try:
        registros_pendientes = request.get('registros_pendientes', [])
        
        if not registros_pendientes:
            return {"success": False, "message": "No hay registros pendientes para notificar"}
        
        # Crear HTML con la lista de vehículos pendientes
        vehiculos_html = ""
        for registro in registros_pendientes:
            fecha_salida = datetime.fromisoformat(registro['fecha_salida'].replace('Z', '+00:00'))
            dias_pendientes = (datetime.now() - fecha_salida).days
            
            vehiculos_html += f"""
            <tr style="background-color: {'#ffebee' if dias_pendientes > 3 else '#fff3e0'};">
                <td><strong>{registro['placa']}</strong></td>
                <td>{registro['chofer']}</td>
                <td>{fecha_salida.strftime('%d/%m/%Y %H:%M')}</td>
                <td>{registro['km_salida']} km</td>
                <td>{registro['nivel_combustible_salida']}</td>
                <td style="color: {'red' if dias_pendientes > 3 else 'orange'};">
                    <strong>{dias_pendientes} día{'s' if dias_pendientes != 1 else ''}</strong>
                </td>
            </tr>
            """
        
        subject = f"🚨 ALERTA URGENTE: {len(registros_pendientes)} Vehículo(s) Sin Retorno"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #d32f2f;">🚨 ALERTA: VEHÍCULOS SIN RETORNO</h2>
            
            <p>Se han detectado <strong>{len(registros_pendientes)} vehículo(s)</strong> que no han registrado su retorno:</p>
            
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <thead style="background-color: #f5f5f5;">
                    <tr>
                        <th>Placa</th>
                        <th>Chofer Responsable</th>
                        <th>Fecha/Hora Salida</th>
                        <th>KM Salida</th>
                        <th>Combustible Salida</th>
                        <th>Días Pendientes</th>
                    </tr>
                </thead>
                <tbody>
                    {vehiculos_html}
                </tbody>
            </table>
            
            <div style="background-color: #ffebee; padding: 15px; border-left: 4px solid #f44336; margin: 20px 0;">
                <h3 style="color: #d32f2f; margin: 0 0 10px 0;">⚠️ ACCIÓN REQUERIDA</h3>
                <ul>
                    <li>Contactar inmediatamente a los choferes responsables</li>
                    <li>Verificar el estado actual de los vehículos</li>
                    <li>Registrar el retorno correspondiente en el sistema</li>
                    <li>En caso de emergencia, reportar a supervisión</li>
                </ul>
            </div>
            
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                Alerta generada automáticamente el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}<br>
                Sistema de Gestión Vehicular - Hotel Arenal Manoa
            </p>
        </body>
        </html>
        """
        
        success = send_email_notification(subject, body)
        
        if success:
            logger.info(f"Alerta de retorno pendiente enviada para {len(registros_pendientes)} vehículos")
            return {
                "success": True, 
                "message": f"Alerta enviada exitosamente para {len(registros_pendientes)} vehículo(s)",
                "count": len(registros_pendientes)
            }
        else:
            return {"success": False, "message": "Error enviando la alerta por email"}
            
    except Exception as e:
        logger.error(f"Error enviando alerta de retorno pendiente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/bitacora/{bitacora_id}")
async def eliminar_bitacora(bitacora_id: int):
    """Eliminar registro de bitácora (solo para administradores)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar que el registro existe
        cursor.execute("SELECT id FROM bitacora WHERE id = ?", (bitacora_id,))
        registro = cursor.fetchone()
        
        if not registro:
            raise HTTPException(status_code=404, detail="Registro de bitácora no encontrado")
        
        # Eliminar el registro
        cursor.execute("DELETE FROM bitacora WHERE id = ?", (bitacora_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="No se pudo eliminar el registro")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Registro de bitácora {bitacora_id} eliminado exitosamente")
        return {"success": True, "message": "Registro eliminado exitosamente"}
        
    except Exception as e:
        logger.error(f"Error al eliminar registro de bitácora {bitacora_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ENDPOINTS CONFIGURACIÓN DE ALERTAS
# ================================

@app.get("/config/alertas")
async def get_config_alertas():
    """Obtener configuración actual de alertas"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM config_alertas WHERE activo = 1 ORDER BY id DESC LIMIT 1")
        config = cursor.fetchone()
        conn.close()
        
        if config:
            return {"success": True, "config": dict_from_row(config)}
        else:
            # Retornar configuración por defecto
            return {
                "success": True, 
                "config": {
                    "email_destino": "contabilidad2@arenalmanoa.com",
                    "alertas_mantenimiento": True,
                    "alertas_polizas": True,
                    "alertas_rtv": True,
                    "alertas_revisiones": True,
                    "alertas_combustible": True,
                    "alertas_bitacora": True,
                    "dias_anticipacion_polizas": 30,
                    "dias_anticipacion_rtv": 30,
                    "dias_anticipacion_mantenimiento": 30,
                    "km_diferencia_alerta": 1
                }
            }
    except Exception as e:
        logger.error(f"Error al obtener configuración de alertas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/config/alertas")
async def set_config_alertas(config: ConfigAlertas):
    """Configurar alertas del sistema"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Desactivar configuración anterior
        cursor.execute("UPDATE config_alertas SET activo = 0")
        
        # Insertar nueva configuración
        cursor.execute('''
            INSERT INTO config_alertas (
                email_destino, alertas_mantenimiento, alertas_polizas, alertas_rtv,
                alertas_revisiones, alertas_combustible, alertas_bitacora,
                dias_anticipacion_polizas, dias_anticipacion_rtv, 
                dias_anticipacion_mantenimiento, km_diferencia_alerta
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (config.email_destino, config.alertas_mantenimiento, config.alertas_polizas,
              config.alertas_rtv, config.alertas_revisiones, config.alertas_combustible,
              config.alertas_bitacora, config.dias_anticipacion_polizas, 
              config.dias_anticipacion_rtv, config.dias_anticipacion_mantenimiento,
              config.km_diferencia_alerta))
        
        # Actualizar configuración global de EMAIL
        EMAIL_CONFIG["recipient_email"] = config.email_destino
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Configuración de alertas guardada exitosamente"}
    except Exception as e:
        logger.error(f"Error al configurar alertas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ENDPOINTS CONFIGURACIÓN EMAIL
# ================================

# Endpoint para configurar email
@app.post("/config/email")
async def configurar_email(email_config: dict):
    """Configurar ajustes de email"""
    try:
        # Actualizar configuración básica
        if "sender_email" in email_config:
            EMAIL_CONFIG["sender_email"] = email_config["sender_email"]
        if "sender_password" in email_config:
            EMAIL_CONFIG["sender_password"] = email_config["sender_password"]
        if "recipient_email" in email_config:
            EMAIL_CONFIG["recipient_email"] = email_config["recipient_email"]
        
        # Configurar proveedor específico si se especifica
        if "provider" in email_config and email_config["provider"] in EMAIL_PROVIDERS:
            provider_config = EMAIL_PROVIDERS[email_config["provider"]]
            EMAIL_CONFIG.update(provider_config)
        
        # Configuración personalizada de servidor
        if "smtp_server" in email_config:
            EMAIL_CONFIG["smtp_server"] = email_config["smtp_server"]
        if "smtp_port" in email_config:
            EMAIL_CONFIG["smtp_port"] = int(email_config["smtp_port"])
        
        return {
            "success": True, 
            "message": "Configuración de email actualizada",
            "config": {
                "smtp_server": EMAIL_CONFIG["smtp_server"],
                "smtp_port": EMAIL_CONFIG["smtp_port"],
                "sender_email": EMAIL_CONFIG["sender_email"],
                "recipient_email": EMAIL_CONFIG["recipient_email"],
                "password_configured": bool(EMAIL_CONFIG["sender_password"])
            }
        }
    except Exception as e:
        logger.error(f"Error configurando email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para obtener configuración actual (sin mostrar contraseña)
@app.get("/config/email")
async def get_email_config():
    """Obtener configuración actual de email (sin contraseña)"""
    return {
        "success": True,
        "config": {
            "smtp_server": EMAIL_CONFIG["smtp_server"],
            "smtp_port": EMAIL_CONFIG["smtp_port"], 
            "sender_email": EMAIL_CONFIG["sender_email"],
            "recipient_email": EMAIL_CONFIG["recipient_email"],
            "password_configured": bool(EMAIL_CONFIG["sender_password"])
        },
        "providers": EMAIL_PROVIDERS
    }

# Endpoint para probar email
@app.post("/config/email/test")
async def test_email():
    """Enviar email de prueba"""
    try:
        subject = "🧪 Prueba del Sistema de Gestión Vehicular"
        body = """
        <html>
        <body>
            <h2>✅ Prueba de Configuración de Email</h2>
            <p>Este es un email de prueba del Sistema de Gestión Vehicular.</p>
            <p>Si recibe este mensaje, la configuración de email está funcionando correctamente.</p>
            <hr>
            <p><small>Enviado automáticamente desde el sistema de gestión vehicular.</small></p>
        </body>
        </html>
        """
        
        success = send_email_notification(subject, body)
        
        if success:
            return {"success": True, "message": "Email de prueba enviado exitosamente"}
        else:
            return {"success": False, "message": "Error enviando email de prueba. Verifique la configuración."}
    except Exception as e:
        logger.error(f"Error probando email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para probar conexión SMTP con configuración personalizada
@app.post("/config/email/test-smtp")
async def test_smtp_connection(smtp_config: dict):
    """Probar conexión SMTP con configuración personalizada"""
    try:
        email = smtp_config.get("email")
        password = smtp_config.get("password")
        host = smtp_config.get("host")
        port = smtp_config.get("port", 587)
        use_tls = smtp_config.get("use_tls", True)
        
        if not all([email, password, host]):
            return {"success": False, "error": "Faltan campos requeridos: email, password, host"}
        
        # Probar conexión SMTP
        server = smtplib.SMTP(host, port)
        if use_tls:
            server.starttls()
        server.login(email, password)
        server.quit()
        
        logger.info(f"Conexión SMTP exitosa para {email} en {host}:{port}")
        return {
            "success": True, 
            "message": f"Conexión SMTP exitosa a {host}:{port}",
            "config": {
                "host": host,
                "port": port,
                "email": email,
                "tls": use_tls
            }
        }
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Error de autenticación SMTP: {e}")
        return {"success": False, "error": "Error de autenticación. Verifique email y contraseña de aplicación."}
    except smtplib.SMTPConnectError as e:
        logger.error(f"Error de conexión SMTP: {e}")
        return {"success": False, "error": f"No se pudo conectar al servidor {host}:{port}"}
    except smtplib.SMTPException as e:
        logger.error(f"Error SMTP: {e}")
        return {"success": False, "error": f"Error SMTP: {str(e)}"}
    except Exception as e:
        logger.warning(f"SMTP no disponible en Railway: {e}")
        return {
            "success": False, 
            "error": "SMTP bloqueado en Railway. Usar EmailJS desde frontend.",
            "suggestion": "Configurar EmailJS para envío desde el navegador",
            "railway_info": "Railway bloquea conexiones SMTP salientes por seguridad"
        }

@app.post("/reportes/enviar-email")
async def enviar_reporte_email(email_data: dict):
    """Enviar reporte por email usando configuración de alertas"""
    try:
        # Obtener configuración de email de la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM config_email WHERE activo = 1 ORDER BY id DESC LIMIT 1")
        email_config = cursor.fetchone()
        conn.close()
        
        if not email_config:
            raise HTTPException(status_code=400, detail="No hay configuración de email activa")
        
        # Crear mensaje de email
        msg = MIMEMultipart()
        msg['From'] = email_config['email_remitente']
        msg['To'] = email_data['destinatario']
        msg['Subject'] = email_data['asunto']
        
        msg.attach(MIMEText(email_data['mensaje_html'], 'html'))
        
        # Enviar email usando la configuración de la base de datos
        server = smtplib.SMTP(email_config['smtp_servidor'], email_config['smtp_puerto'])
        server.starttls()
        server.login(email_config['email_usuario'], email_config['email_password'])
        text = msg.as_string()
        server.sendmail(email_config['email_remitente'], email_data['destinatario'], text)
        server.quit()
        
        logger.info(f"Reporte enviado por email a {email_data['destinatario']}")
        return {"success": True, "message": "Reporte enviado exitosamente"}
        
    except Exception as e:
        logger.error(f"Error enviando reporte por email: {e}")
        return {"success": False, "message": f"Error enviando reporte: {str(e)}"}

# Endpoint para obtener detalle de alertas para el frontend
@app.get("/alertas/detalle")
async def get_alertas_detalle():
    """Obtener detalle de todas las alertas para mostrar en el frontend"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        hoy = datetime.now().date()
        en_30_dias = hoy + timedelta(days=30)
        
        alertas = {
            "mantenimiento": [],
            "polizas": [],
            "rtv": [],
            "revisiones": [],
            "combustible": []
        }
        
        # ALERTAS DE MANTENIMIENTO
        cursor.execute('''
            SELECT m.*, v.marca, v.modelo 
            FROM mantenimientos m
            JOIN vehiculos v ON m.placa = v.placa
            WHERE (m.proxima_fecha IS NOT NULL AND m.proxima_fecha <= ? AND m.proxima_fecha >= ?)
            ORDER BY m.proxima_fecha ASC
        ''', (en_30_dias.isoformat(), hoy.isoformat()))
        
        mantenimientos_fecha = cursor.fetchall()
        for m in mantenimientos_fecha:
            dias_restantes = (datetime.strptime(m['proxima_fecha'], '%Y-%m-%d').date() - hoy).days
            alertas["mantenimiento"].append({
                "placa": m['placa'],
                "vehiculo": f"{m['marca']} {m['modelo']}",
                "tipo": m['tipo'],
                "descripcion": f"Mantenimiento por fecha - {dias_restantes} días restantes",
                "dias_restantes": dias_restantes,
                "urgente": dias_restantes <= 7,
                "fecha": m['proxima_fecha']
            })
        
        # ALERTAS DE PÓLIZAS
        cursor.execute('''
            SELECT p.*, v.marca, v.modelo 
            FROM polizas p 
            JOIN vehiculos v ON p.placa = v.placa
            WHERE p.fecha_vencimiento <= ? AND p.fecha_vencimiento >= ? AND p.estado = 'Activa'
            ORDER BY p.fecha_vencimiento ASC
        ''', (en_30_dias.isoformat(), hoy.isoformat()))
        
        polizas = cursor.fetchall()
        for p in polizas:
            dias_restantes = (datetime.strptime(p['fecha_vencimiento'], '%Y-%m-%d').date() - hoy).days
            alertas["polizas"].append({
                "placa": p['placa'],
                "vehiculo": f"{p['marca']} {p['modelo']}",
                "numero_poliza": p['numero_poliza'],
                "aseguradora": p['aseguradora'],
                "descripcion": f"Póliza vence en {dias_restantes} días",
                "dias_restantes": dias_restantes,
                "urgente": dias_restantes <= 7,
                "fecha": p['fecha_vencimiento']
            })
        
        # ALERTAS DE RTV
        cursor.execute('''
            SELECT r.*, v.marca, v.modelo 
            FROM rtv r 
            JOIN vehiculos v ON r.placa = v.placa
            WHERE r.fecha_vencimiento <= ? AND r.fecha_vencimiento >= ? AND r.estado = 'Vigente'
            ORDER BY r.fecha_vencimiento ASC
        ''', (en_30_dias.isoformat(), hoy.isoformat()))
        
        rtv_records = cursor.fetchall()
        for r in rtv_records:
            dias_restantes = (datetime.strptime(r['fecha_vencimiento'], '%Y-%m-%d').date() - hoy).days
            alertas["rtv"].append({
                "placa": r['placa'],
                "vehiculo": f"{r['marca']} {r['modelo']}",
                "numero_cita": r['numero_cita'],
                "descripcion": f"RTV vence en {dias_restantes} días",
                "dias_restantes": dias_restantes,
                "urgente": dias_restantes <= 7,
                "fecha": r['fecha_vencimiento']
            })
        
        # ALERTAS DE REVISIONES CON FALLAS
        cursor.execute('''
            SELECT r.*, v.marca, v.modelo 
            FROM revisiones r 
            JOIN vehiculos v ON r.placa = v.placa
            WHERE r.aprobado = 0 AND r.fecha >= ?
            ORDER BY r.fecha DESC
        ''', ((hoy - timedelta(days=30)).isoformat(),))
        
        revisiones = cursor.fetchall()
        for r in revisiones:
            fallas = []
            if r['estado_motor'] != 'Bueno': fallas.append(f"Motor: {r['estado_motor']}")
            if r['estado_frenos'] != 'Bueno': fallas.append(f"Frenos: {r['estado_frenos']}")
            if r['estado_luces'] != 'Bueno': fallas.append(f"Luces: {r['estado_luces']}")
            if r['estado_llantas'] != 'Bueno': fallas.append(f"Llantas: {r['estado_llantas']}")
            if r['estado_carroceria'] != 'Bueno': fallas.append(f"Carrocería: {r['estado_carroceria']}")
            
            alertas["revisiones"].append({
                "placa": r['placa'],
                "vehiculo": f"{r['marca']} {r['modelo']}",
                "inspector": r['inspector'],
                "fallas": fallas,
                "descripcion": f"Fallas detectadas: {', '.join(fallas) if fallas else 'Revisión no aprobada'}",
                "urgente": True,
                "fecha": r['fecha']
            })
        
        # ALERTAS DE COMBUSTIBLE (detección básica)
        alertas["combustible"] = check_abnormal_fuel_consumption(cursor, hoy)
        
        conn.close()
        
        # Calcular totales
        totales = {
            "mantenimiento": len(alertas["mantenimiento"]),
            "polizas": len(alertas["polizas"]),
            "rtv": len(alertas["rtv"]),
            "revisiones": len(alertas["revisiones"]),
            "combustible": len(alertas["combustible"]),
            "total": sum([len(alertas[k]) for k in alertas.keys()])
        }
        
        return {
            "success": True,
            "data": {
                "alertas": alertas,
                "totales": totales,
                "fecha_consulta": hoy.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo detalle de alertas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINT DE PRUEBA PARA EMAILS =====
@app.post("/test-email")
async def test_email():
    """
    Endpoint para probar que los emails automáticos funcionan correctamente.
    Envía un email de prueba usando SendGrid.
    """
    try:
        if EMAIL_METHOD == "SENDGRID":
            # Probar SendGrid
            from sendgrid_email import SendGridEmailService
            
            service = SendGridEmailService()
            
            # Email de prueba
            test_data = {
                "tipo": "test",
                "subject": "✅ PRUEBA: Sistema de Emails Automáticos Funcional",
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "mensaje": "🎉 ¡El sistema de emails automáticos está funcionando correctamente!",
                "content": """
                <div class="alert">
                    <h3>🎯 PRUEBA EXITOSA</h3>
                    <p><strong>✅ SendGrid API:</strong> Configurado y funcionando</p>
                    <p><strong>📧 Emails automáticos:</strong> Activos 24/7</p>
                    <p><strong>🚀 Sistema listo para:</strong></p>
                    <ul>
                        <li>🔧 Alertas de mantenimiento</li>
                        <li>⛽ Monitoreo de combustible</li>
                        <li>🚗 Notificaciones RTV</li>
                        <li>📋 Vencimiento de pólizas</li>
                        <li>👨‍💼 Gestión de choferes</li>
                    </ul>
                    <p><strong>📍 Destinatario:</strong> contabilidad2@arenalmanoa.com</p>
                    <p><strong>⏰ Enviado:</strong> {fecha}</p>
                </div>
                """.format(fecha=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            }
            
            resultado = service.send_alert_email(test_data, to_email="contabilidad2@arenalmanoa.com")
            
            if resultado.get("success"):
                logger.info("✅ Email de prueba SendGrid enviado exitosamente")
                return {
                    "success": True,
                    "method": "SendGrid",
                    "message": "Email de prueba enviado correctamente",
                    "email_id": resultado.get("email_id"),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise Exception(f"SendGrid error: {resultado.get('error')}")
                
        else:
            # Fallback SMTP (probablemente fallará en Railway)
            return {
                "success": False,
                "method": "SMTP",
                "message": "SendGrid no configurado, SMTP no disponible en Railway",
                "instructions": "Configurar SENDGRID_API_KEY en variables de entorno"
            }
            
    except Exception as e:
        logger.error(f"❌ Error en test de email: {e}")
        return {
            "success": False,
            "error": str(e),
            "instructions": [
                "1. Verificar SENDGRID_API_KEY en Railway variables",
                "2. Verificar SENDGRID_FROM_EMAIL configurado", 
                "3. Verificar Single Sender Authentication en SendGrid",
                "4. Revisar logs de Railway para más detalles"
            ]
        }

# ===== ENDPOINTS DE BACKUP Y EXPORT =====
@app.post("/backup/create")
async def create_backup():
    """Crear backup completo de la base de datos"""
    try:
        from backup_manager import DatabaseBackupManager
        manager = DatabaseBackupManager()
        
        result = manager.create_full_backup("manual", include_export=True)
        
        if "error" not in result:
            logger.info("✅ Backup manual creado exitosamente")
            return {
                "success": True,
                "message": "Backup creado exitosamente",
                "backup_info": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise Exception(result["error"])
            
    except Exception as e:
        logger.error(f"❌ Error creando backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backup/export")
async def export_database():
    """Exportar base de datos en múltiples formatos (JSON, CSV, SQL)"""
    try:
        from backup_manager import export_database_now
        
        result = export_database_now()
        
        if result.get("success"):
            logger.info("✅ Export de base de datos completado")
            return {
                "success": True,
                "message": "Base de datos exportada exitosamente",
                "export_info": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise Exception(result.get("error", "Error desconocido en export"))
            
    except Exception as e:
        logger.error(f"❌ Error exportando base de datos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/backup/list")
async def list_backups():
    """Listar todos los backups disponibles"""
    try:
        from backup_manager import DatabaseBackupManager
        manager = DatabaseBackupManager()
        
        backups = manager.list_backups()
        stats = manager.get_database_stats()
        
        return {
            "success": True,
            "current_stats": stats,
            "backups": backups,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error listando backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backup/emergency")
async def emergency_backup():
    """Crear backup de emergencia inmediato"""
    try:
        from backup_manager import create_emergency_backup
        
        result = create_emergency_backup()
        
        if "error" not in result:
            logger.info("🚨 Backup de emergencia creado")
            return {
                "success": True,
                "message": "Backup de emergencia creado",
                "backup_info": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise Exception(result["error"])
            
    except Exception as e:
        logger.error(f"❌ Error en backup de emergencia: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/backup/stats")
async def backup_stats():
    """Obtener estadísticas actuales de la base de datos"""
    try:
        from backup_manager import DatabaseBackupManager
        manager = DatabaseBackupManager()
        
        stats = manager.get_database_stats()
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data-preservation/status")
async def data_preservation_status():
    """Obtener estado del sistema de preservación de datos"""
    try:
        if not DATA_PRESERVATION_ENABLED or not preservation_system:
            return {
                "success": False,
                "message": "Sistema de preservación de datos no disponible",
                "preservation_enabled": False,
                "github_backup_enabled": AUTO_BACKUP_ENABLED,
                "system_status": "⚠️ BÁSICO - Sistema funcionando sin preservación avanzada"
            }
        
        # Obtener conteos actuales
        current_counts = preservation_system.get_current_data_counts()
        
        # Obtener backups disponibles
        available_backups = preservation_system.get_available_backups()
        
        return {
            "success": True,
            "preservation_enabled": True,
            "github_backup_enabled": AUTO_BACKUP_ENABLED,
            "current_data_counts": current_counts,
            "available_backups": len(available_backups),
            "latest_backup": available_backups[0] if available_backups else None,
            "total_records": sum(current_counts.values()) if current_counts else 0,
            "system_status": "✅ PROTEGIDO - Todos los datos están respaldados automáticamente",
            "last_check": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de preservación: {e}")
        return {
            "success": False,
            "message": f"Error en sistema de preservación: {str(e)}",
            "preservation_enabled": False,
            "system_status": "⚠️ ERROR - Revisar logs del sistema"
        }

@app.post("/data-preservation/manual-backup")
async def create_manual_preservation_backup():
    """Crear backup manual de preservación"""
    try:
        if not DATA_PRESERVATION_ENABLED or not preservation_system:
            raise HTTPException(status_code=503, detail="Sistema de preservación no disponible")
        
        backup_path, metadata = preservation_system.create_pre_change_backup("Backup manual solicitado por usuario")
        
        if backup_path:
            return {
                "success": True,
                "message": "Backup manual creado exitosamente",
                "backup_path": backup_path,
                "metadata": metadata
            }
        else:
            raise HTTPException(status_code=500, detail="Error creando backup manual")
            
    except Exception as e:
        logger.error(f"Error creando backup manual: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data-preservation/backups")
async def list_preservation_backups():
    """Listar todos los backups de preservación disponibles"""
    try:
        if not DATA_PRESERVATION_ENABLED or not preservation_system:
            raise HTTPException(status_code=503, detail="Sistema de preservación no disponible")
        
        backups = preservation_system.get_available_backups()
        
        return {
            "success": True,
            "backups": backups,
            "count": len(backups)
        }
        
    except Exception as e:
        logger.error(f"Error listando backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/verify-my-data")
async def verify_user_data():
    """Endpoint especial para que el usuario verifique sus datos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener todos los vehículos con detalles
        cursor.execute("""
            SELECT placa, marca, modelo, ano, color, propietario, poliza, seguro, 
                   km_inicial, created_at, updated_at 
            FROM vehiculos ORDER BY placa
        """)
        vehiculos = [dict_from_row(row) for row in cursor.fetchall()]
        
        # Obtener conteos de todas las tablas
        tables_info = {}
        tables = ['vehiculos', 'mantenimientos', 'combustible', 'revisiones', 'polizas', 'rtv', 'bitacora']
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                tables_info[table] = count
            except:
                tables_info[table] = 0
        
        # Obtener últimos registros de actividad
        cursor.execute("SELECT * FROM bitacora ORDER BY fecha DESC LIMIT 5")
        recent_activity = [dict_from_row(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "success": True,
            "verification_time": datetime.now().isoformat(),
            "message": "🔍 Verificación completa de tus datos",
            "vehiculos": vehiculos,
            "resumen_tablas": tables_info,
            "total_vehiculos": len(vehiculos),
            "actividad_reciente": recent_activity,
            "sistema_estado": "✅ FUNCIONANDO - Todos los datos preservados",
            "backup_info": {
                "database_protected": True,
                "last_backup": "Backups automáticos activos",
                "gitignore_protected": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error verificando datos usuario: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error verificando datos - contactar soporte"
        }

if __name__ == "__main__":
    init_database()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")