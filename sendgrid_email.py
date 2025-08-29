#!/usr/bin/env python3
"""
Sistema de Email usando SendGrid API para Railway
Reemplaza SMTP que está bloqueado en Railway
"""

import os
import requests
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SendGridEmailService:
    """Servicio de email usando SendGrid API"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('SENDGRID_API_KEY')
        self.base_url = "https://api.sendgrid.com/v3"
        self.from_email = "sistema@vehicular-app.com"  # Cambiar por tu dominio
        
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Enviar email usando SendGrid API"""
        
        if not self.api_key:
            logger.warning("⚠️ SendGrid API key no configurada")
            return {"success": False, "error": "API key no configurada"}
        
        # Preparar datos para SendGrid
        data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject
                }
            ],
            "from": {"email": self.from_email, "name": "Sistema Vehicular"},
            "content": [
                {
                    "type": "text/html",
                    "value": html_content
                }
            ]
        }
        
        if text_content:
            data["content"].insert(0, {
                "type": "text/plain", 
                "value": text_content
            })
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/mail/send",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 202:
                logger.info(f"✅ Email enviado exitosamente a {to_email}")
                return {"success": True, "message": "Email enviado"}
            else:
                error_msg = f"Error SendGrid {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            logger.error(f"❌ Error enviando email: {e}")
            return {"success": False, "error": str(e)}
    
    def send_alert_email(self, alert_data):
        """Enviar email de alerta del sistema vehicular"""
        
        # HTML template para alertas
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .header {{ background: #d32f2f; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f5f5f5; }}
                .alert {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #ff9800; }}
                .critical {{ border-left-color: #d32f2f; }}
                .footer {{ text-align: center; color: #666; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚨 ALERTA SISTEMA VEHICULAR</h1>
                <p>Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            <div class="content">
                <h2>Resumen de Alertas</h2>
                {alert_data.get('content', 'Sin detalles específicos')}
                
                <div class="alert critical">
                    <strong>⚡ ACCIÓN REQUERIDA:</strong>
                    <ul>
                        <li>Revisar inmediatamente las alertas críticas</li>
                        <li>Programar mantenimientos pendientes</li>
                        <li>Renovar pólizas y RTV próximas a vencer</li>
                        <li>Contactar choferes con retornos pendientes</li>
                    </ul>
                </div>
            </div>
            <div class="footer">
                <p><small>Sistema de Gestión Vehicular - Alerta Automática</small></p>
                <p><small>Para más detalles, acceda al sistema en línea</small></p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to_email=alert_data.get('recipient', 'contabilidad2@arenalmanoa.com'),
            subject=alert_data.get('subject', '🚨 Alerta Sistema Vehicular'),
            html_content=html_template
        )

# Función global para usar en main.py
email_service = SendGridEmailService()

def send_system_email(recipient, subject, html_content):
    """Función compatible con el sistema actual"""
    return email_service.send_email(recipient, subject, html_content)

def send_alert_notification(alert_data):
    """Enviar notificación de alerta"""
    return email_service.send_alert_email(alert_data)