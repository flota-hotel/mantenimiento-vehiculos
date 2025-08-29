#!/usr/bin/env python3
"""
Test Completo Local - Emails y Backup
Probar toda la funcionalidad sin depender de Railway
"""

import os
import sys
import json
from datetime import datetime

# Configurar environment para testing (USAR TUS VARIABLES REALES)
# IMPORTANTE: Configurar estas variables antes de ejecutar
if not os.environ.get('SENDGRID_API_KEY'):
    print("❌ SENDGRID_API_KEY no configurada")
    print("Ejecutar: export SENDGRID_API_KEY='SG.tu_api_key_aqui'")
    sys.exit(1)

os.environ.setdefault('SENDGRID_FROM_EMAIL', 'contabilidad2@arenalmanoa.com')
os.environ.setdefault('SENDGRID_FROM_NAME', 'Sistema Vehicular Hotel Arenal')

def test_sendgrid_email():
    """Probar envío de email directo con SendGrid"""
    print("📧 PROBANDO SENDGRID EMAIL...")
    print("=" * 50)
    
    try:
        from sendgrid_email import SendGridEmailService
        
        service = SendGridEmailService()
        print(f"✅ Servicio inicializado")
        print(f"📧 From Email: {service.from_email}")
        print(f"👤 From Name: {service.from_name}")
        print(f"🔑 API Key: {service.api_key[:10]}...")
        
        # Test email data
        test_data = {
            "tipo": "test_local",
            "subject": "✅ PRUEBA LOCAL: Sistema de Emails Funcionando",
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mensaje": "🎉 ¡Test local exitoso! SendGrid configurado correctamente",
            "content": f"""
            <div class="alert">
                <h3>🎯 PRUEBA LOCAL EXITOSA</h3>
                <p><strong>⚡ Estado:</strong> SendGrid API funcionando</p>
                <p><strong>📧 Destinatario:</strong> contabilidad2@arenalmanoa.com</p>
                <p><strong>⏰ Enviado:</strong> {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</p>
                <p><strong>🚀 Próximo paso:</strong> Verificar Railway deployment</p>
                
                <h4>🔧 Sistema listo para:</h4>
                <ul>
                    <li>✅ Alertas de mantenimiento automáticas</li>
                    <li>✅ Monitoreo de combustible</li>
                    <li>✅ Notificaciones RTV</li>
                    <li>✅ Vencimiento de pólizas</li>
                    <li>✅ Gestión de choferes</li>
                </ul>
                
                <p><strong>💯 Conclusión:</strong> Email automático FUNCIONANDO</p>
            </div>
            """
        }
        
        print(f"🚀 Enviando email de prueba...")
        resultado = service.send_alert_email(test_data, to_email="contabilidad2@arenalmanoa.com")
        
        if resultado.get("success"):
            print(f"✅ EMAIL ENVIADO EXITOSAMENTE!")
            print(f"📬 Email ID: {resultado.get('email_id', 'N/A')}")
            print(f"📧 Revisa: contabilidad2@arenalmanoa.com")
            return True
        else:
            print(f"❌ Error enviando email: {resultado.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False

def test_backup_system():
    """Probar sistema de backup"""
    print("\n🗄️ PROBANDO SISTEMA DE BACKUP...")
    print("=" * 50)
    
    try:
        from backup_manager import DatabaseBackupManager, export_database_now
        
        manager = DatabaseBackupManager()
        
        # Estadísticas actuales
        print("📊 Estadísticas actuales:")
        stats = manager.get_database_stats()
        total_records = 0
        
        for table, count in stats.items():
            if isinstance(count, int):
                print(f"  {table}: {count:,} registros")
                total_records += count
        
        print(f"\n🎯 TOTAL PROTEGIDO: {total_records:,} registros")
        
        # Test backup creation
        print(f"\n🔄 Creando backup de prueba...")
        backup_result = manager.create_full_backup("manual", include_export=True)
        
        if "error" not in backup_result:
            print(f"✅ BACKUP CREADO EXITOSAMENTE!")
            
            # Mostrar archivos creados
            if "zip_backup" in backup_result:
                print(f"📦 ZIP: {backup_result['zip_backup']}")
            if "sqlite_backup" in backup_result:
                print(f"🗄️ SQLite: {backup_result['sqlite_backup']}")
            if "json_export" in backup_result:
                print(f"📄 JSON: {backup_result['json_export']}")
            if "csv_export" in backup_result:
                print(f"📊 CSV: {backup_result['csv_export']}")
                
            # Verificar integridad
            integrity = backup_result.get("integrity_check", {})
            if integrity.get("valid"):
                print(f"✅ Integridad verificada: OK")
            
            return True
        else:
            print(f"❌ Error en backup: {backup_result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción en backup: {e}")
        return False

def test_export_system():
    """Probar sistema de export"""
    print(f"\n📤 PROBANDO EXPORT COMPLETO...")
    print("=" * 50)
    
    try:
        from backup_manager import export_database_now
        
        result = export_database_now()
        
        if result.get("success"):
            print(f"✅ EXPORT COMPLETADO!")
            
            files = result.get("files", {})
            print(f"\n📁 Archivos creados:")
            
            for file_type, path in files.items():
                if os.path.exists(path):
                    size = os.path.getsize(path) / 1024  # KB
                    print(f"  {file_type}: {path} ({size:.1f} KB)")
            
            return True
        else:
            print(f"❌ Error en export: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción en export: {e}")
        return False

def main():
    """Ejecutar todos los tests"""
    print("🧪 TEST COMPLETO SISTEMA VEHICULAR")
    print(f"⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {}
    
    # Test 1: SendGrid Email
    results['email'] = test_sendgrid_email()
    
    # Test 2: Backup System  
    results['backup'] = test_backup_system()
    
    # Test 3: Export System
    results['export'] = test_export_system()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE TESTS")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name.upper()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print(f"\n🎉 ¡TODOS LOS SISTEMAS FUNCIONANDO!")
        print(f"📧 Check email: contabilidad2@arenalmanoa.com")
        print(f"📁 Check backups: /home/user/webapp/backups/")
        print(f"🚀 Sistema listo para producción")
    else:
        print(f"\n⚠️ Algunos tests fallaron - revisar configuración")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)