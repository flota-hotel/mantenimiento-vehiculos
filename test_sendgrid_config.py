#!/usr/bin/env python3
"""
Test Script para verificar configuración SendGrid
Ejecutar después de configurar las variables de entorno en Railway
"""

import os
import sys
from datetime import datetime

def test_sendgrid_configuration():
    """Verifica que SendGrid esté configurado correctamente"""
    
    print("🔍 VERIFICANDO CONFIGURACIÓN SENDGRID...")
    print("=" * 50)
    
    # 1. Verificar variables de entorno
    print("1️⃣ Verificando variables de entorno:")
    
    api_key = os.environ.get('SENDGRID_API_KEY')
    from_email = os.environ.get('SENDGRID_FROM_EMAIL')
    from_name = os.environ.get('SENDGRID_FROM_NAME', 'Sistema Vehicular')
    
    if not api_key:
        print("❌ SENDGRID_API_KEY no configurada")
        return False
    
    if not from_email:
        print("❌ SENDGRID_FROM_EMAIL no configurada")
        return False
    
    print(f"✅ SENDGRID_API_KEY: {api_key[:10]}...")
    print(f"✅ SENDGRID_FROM_EMAIL: {from_email}")
    print(f"✅ SENDGRID_FROM_NAME: {from_name}")
    
    # 2. Verificar importación del módulo
    print("\n2️⃣ Verificando módulo SendGrid:")
    try:
        from sendgrid_email import SendGridEmailService
        print("✅ Módulo sendgrid_email importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando sendgrid_email: {e}")
        return False
    
    # 3. Verificar inicialización del servicio
    print("\n3️⃣ Inicializando servicio SendGrid:")
    try:
        service = SendGridEmailService()
        print("✅ Servicio SendGrid inicializado")
    except Exception as e:
        print(f"❌ Error inicializando SendGrid: {e}")
        return False
    
    # 4. Probar envío de email
    print("\n4️⃣ Probando envío de email de prueba:")
    try:
        test_data = {
            "tipo": "configuracion_test",
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mensaje": "🎉 Configuración SendGrid completada exitosamente",
            "detalles": [
                "✅ Variables de entorno configuradas",
                "✅ API Key válida",
                "✅ Servicio inicializado", 
                "✅ Email de prueba enviado",
                "🚀 Sistema listo para enviar alertas automáticas"
            ]
        }
        
        resultado = service.send_alert_email(test_data)
        
        if resultado.get("success"):
            print(f"✅ Email de prueba enviado exitosamente")
            print(f"📧 Email ID: {resultado.get('email_id', 'N/A')}")
            return True
        else:
            print(f"❌ Error enviando email: {resultado.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error en envío de prueba: {e}")
        return False

def print_configuration_guide():
    """Muestra guía de configuración si algo falla"""
    
    print("\n" + "=" * 60)
    print("🔧 GUÍA DE CONFIGURACIÓN SENDGRID")
    print("=" * 60)
    
    print("\n📝 PASO 1: Variables de entorno en Railway")
    print("   Agregar en Railway Dashboard → Variables:")
    print("   • SENDGRID_API_KEY=SG.tu_api_key_completa")
    print("   • SENDGRID_FROM_EMAIL=contabilidad2@arenalmanoa.com")
    print("   • SENDGRID_FROM_NAME=Sistema Vehicular Hotel Arenal")
    
    print("\n🔑 PASO 2: Crear API Key en SendGrid")
    print("   1. Ir a https://app.sendgrid.com/settings/api_keys")
    print("   2. Create API Key → Full Access")
    print("   3. Copiar el API Key (SG.xxx...)")
    
    print("\n📧 PASO 3: Verificar Single Sender")
    print("   1. Settings → Sender Authentication → Single Sender Verification")
    print("   2. Agregar: contabilidad2@arenalmanoa.com")
    print("   3. Verificar el email recibido")
    
    print("\n🚀 PASO 4: Verificar deployment")
    print("   • Railway redespliega automáticamente")
    print("   • Logs muestran: '✅ SendGrid email service loaded'")
    print("   • Ejecutar: curl -X POST https://tu-app.up.railway.app/test-email")

if __name__ == "__main__":
    print("🚀 TEST DE CONFIGURACIÓN SENDGRID")
    print("Timestamp:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    success = test_sendgrid_configuration()
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 ¡CONFIGURACIÓN SENDGRID COMPLETADA!")
        print("=" * 50)
        print("✅ Sistema listo para enviar emails automáticos")
        print("📧 Alertas de mantenimiento, combustible, RTV funcionando")
        print("🔄 Emails se envían automáticamente 24/7")
        print("\n🌐 Para probar desde web:")
        print("   POST https://tu-app.up.railway.app/test-email")
    else:
        print("\n" + "=" * 50)
        print("❌ CONFIGURACIÓN INCOMPLETA")
        print("=" * 50)
        print_configuration_guide()
    
    sys.exit(0 if success else 1)