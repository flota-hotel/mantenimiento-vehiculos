#!/usr/bin/env python3
"""
Railway Status Checker y Troubleshooter
Verificar y diagnosticar problemas de Railway
"""

import requests
import time
import json
from datetime import datetime

RAILWAY_URL = "https://mantenimiento-vehiculos-production.up.railway.app"

def check_railway_status():
    """Verificar estado de Railway"""
    print("🔍 VERIFICANDO ESTADO DE RAILWAY")
    print("=" * 50)
    print(f"URL: {RAILWAY_URL}")
    
    tests = [
        ("Root endpoint", "/"),
        ("Health check", "/vehiculos"),  
        ("Email config", "/config/email"),
        ("Backup stats", "/backup/stats"),
        ("Test email", "/test-email")
    ]
    
    results = {}
    
    for name, endpoint in tests:
        url = f"{RAILWAY_URL}{endpoint}"
        print(f"\n🧪 Testing {name}: {endpoint}")
        
        try:
            if endpoint == "/test-email":
                # POST request for email test
                response = requests.post(url, timeout=30, headers={'Content-Type': 'application/json'})
            else:
                # GET request for others  
                response = requests.get(url, timeout=30)
            
            status = response.status_code
            
            if status == 200:
                print(f"✅ {name}: OK (200)")
                try:
                    data = response.json()
                    if endpoint == "/backup/stats" and data.get("success"):
                        stats = data.get("stats", {})
                        total = sum([v for v in stats.values() if isinstance(v, int)])
                        print(f"   📊 DB Records: {total:,}")
                    elif endpoint == "/test-email" and data.get("success"):
                        print(f"   📧 Email sent successfully!")
                    elif endpoint == "/config/email":
                        print(f"   ⚙️ Email config loaded")
                except:
                    print(f"   📄 Response received (not JSON)")
                
                results[name] = "OK"
            else:
                print(f"❌ {name}: HTTP {status}")
                results[name] = f"HTTP {status}"
                
        except requests.exceptions.Timeout:
            print(f"⏱️ {name}: TIMEOUT (>30s)")
            results[name] = "TIMEOUT"
            
        except requests.exceptions.ConnectionError:
            print(f"🔌 {name}: CONNECTION ERROR")
            results[name] = "CONNECTION_ERROR"
            
        except Exception as e:
            print(f"❌ {name}: ERROR - {str(e)[:50]}...")
            results[name] = f"ERROR: {type(e).__name__}"
    
    return results

def diagnose_issues(results):
    """Diagnosticar problemas basado en resultados"""
    print("\n" + "=" * 50)
    print("🔧 DIAGNÓSTICO Y RECOMENDACIONES")
    print("=" * 50)
    
    working = [k for k, v in results.items() if v == "OK"]
    failing = [k for k, v in results.items() if v != "OK"]
    
    print(f"✅ Funcionando: {len(working)}/{len(results)}")
    print(f"❌ Con problemas: {len(failing)}/{len(results)}")
    
    if len(working) == 0:
        print("\n🚨 RAILWAY COMPLETAMENTE INACCESIBLE")
        print("Posibles causas:")
        print("• Deploy en progreso (esperar 5-10 minutos)")
        print("• Error en el código (revisar logs)")
        print("• Problema de Railway (status.railway.app)")
        print("• Variables de entorno faltantes")
        
        print("\n🔧 ACCIONES RECOMENDADAS:")
        print("1. Esperar 5 minutos y volver a probar")
        print("2. Revisar Railway Dashboard → Deployments → Logs")
        print("3. Verificar variables: SENDGRID_API_KEY, SENDGRID_FROM_EMAIL")
        print("4. Hacer redeploy manual si es necesario")
        
    elif len(working) < len(results):
        print(f"\n⚠️ RAILWAY PARCIALMENTE FUNCIONAL")
        print(f"✅ Funciona: {', '.join(working)}")
        print(f"❌ Falla: {', '.join(failing)}")
        
        if "Test email" in failing:
            print("\n📧 EMAIL ISSUE:")
            print("• Verificar SENDGRID_API_KEY en Railway variables")
            print("• Verificar SENDGRID_FROM_EMAIL configurado")
            print("• Confirmar Single Sender en SendGrid")
        
        if "Backup stats" in failing:
            print("\n🗄️ BACKUP ISSUE:")
            print("• Verificar permisos de escritura")
            print("• Confirmar pandas instalado")
            
    else:
        print(f"\n🎉 RAILWAY FUNCIONANDO PERFECTAMENTE")
        print("✅ Todos los endpoints responden correctamente")
        print("✅ Sistema listo para uso en producción")
    
    return len(working) == len(results)

def wait_and_retry():
    """Esperar y reintentar hasta que Railway funcione"""
    print(f"\n⏰ ESPERANDO RAILWAY DEPLOYMENT...")
    
    max_attempts = 10
    wait_time = 60  # segundos
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n🔄 Intento {attempt}/{max_attempts}")
        
        results = check_railway_status()
        all_working = diagnose_issues(results)
        
        if all_working:
            print(f"\n🎉 ¡RAILWAY FUNCIONANDO EN INTENTO {attempt}!")
            return True
        
        if attempt < max_attempts:
            print(f"\n⏳ Esperando {wait_time}s antes del próximo intento...")
            time.sleep(wait_time)
    
    print(f"\n❌ Railway no respondió después de {max_attempts} intentos")
    print("🔧 Revisar manualmente Railway Dashboard")
    return False

def main():
    """Función principal"""
    print("🚀 RAILWAY STATUS CHECKER")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test inicial
    results = check_railway_status()
    all_working = diagnose_issues(results)
    
    if not all_working:
        print(f"\n🔄 Railway necesita tiempo para estabilizarse...")
        wait_and_retry()

if __name__ == "__main__":
    main()