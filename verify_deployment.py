#!/usr/bin/env python3
"""
Script para verificar que el deployment en Railway tiene todos los datos
Uso: python3 verify_deployment.py [URL_DE_RAILWAY]
Ejemplo: python3 verify_deployment.py https://tu-app.railway.app
"""

import sys
import requests
import json

def verify_deployment(base_url):
    """Verificar que el deployment tenga todos los datos correctos"""
    
    print("=" * 60)
    print("🔍 VERIFICACIÓN DE DEPLOYMENT EN RAILWAY")
    print("=" * 60)
    print(f"\n🌐 URL Base: {base_url}\n")
    
    # Eliminar trailing slash
    base_url = base_url.rstrip('/')
    
    results = {
        "success": [],
        "warnings": [],
        "errors": []
    }
    
    # 1. Verificar health endpoint
    print("1️⃣ Verificando health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Health endpoint responde correctamente")
            results["success"].append("Health endpoint OK")
        else:
            print(f"   ⚠️ Health endpoint retornó código {response.status_code}")
            results["warnings"].append(f"Health endpoint: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error en health endpoint: {e}")
        results["errors"].append(f"Health endpoint: {e}")
    
    # 2. Verificar vehículos
    print("\n2️⃣ Verificando vehículos...")
    try:
        response = requests.get(f"{base_url}/vehiculos", timeout=10)
        if response.status_code == 200:
            vehiculos = response.json()
            count = len(vehiculos)
            print(f"   ✅ {count} vehículos encontrados")
            if count >= 16:
                results["success"].append(f"Vehículos: {count}")
            else:
                results["warnings"].append(f"Solo {count} vehículos (esperado: 16)")
        else:
            print(f"   ⚠️ Error obteniendo vehículos: {response.status_code}")
            results["warnings"].append(f"Vehículos: Error {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error en vehículos: {e}")
        results["errors"].append(f"Vehículos: {e}")
    
    # 3. Verificar bitácora
    print("\n3️⃣ Verificando bitácora...")
    try:
        response = requests.get(f"{base_url}/bitacora", timeout=10)
        if response.status_code == 200:
            bitacora = response.json()
            count = len(bitacora)
            print(f"   ✅ {count} registros de bitácora encontrados")
            if count >= 300:
                results["success"].append(f"Bitácora: {count}")
            else:
                results["warnings"].append(f"Solo {count} registros de bitácora (esperado: ~363)")
        else:
            print(f"   ⚠️ Error obteniendo bitácora: {response.status_code}")
            results["warnings"].append(f"Bitácora: Error {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error en bitácora: {e}")
        results["errors"].append(f"Bitácora: {e}")
    
    # 4. Verificar combustible
    print("\n4️⃣ Verificando combustible...")
    try:
        response = requests.get(f"{base_url}/combustible", timeout=10)
        if response.status_code == 200:
            combustible = response.json()
            count = len(combustible)
            print(f"   ✅ {count} registros de combustible encontrados")
            if count >= 40:
                results["success"].append(f"Combustible: {count}")
            else:
                results["warnings"].append(f"Solo {count} registros de combustible (esperado: ~47)")
        else:
            print(f"   ⚠️ Error obteniendo combustible: {response.status_code}")
            results["warnings"].append(f"Combustible: Error {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error en combustible: {e}")
        results["errors"].append(f"Combustible: {e}")
    
    # 5. Verificar mantenimientos
    print("\n5️⃣ Verificando mantenimientos...")
    try:
        response = requests.get(f"{base_url}/mantenimientos", timeout=10)
        if response.status_code == 200:
            mantenimientos = response.json()
            count = len(mantenimientos)
            print(f"   ✅ {count} mantenimientos encontrados")
            results["success"].append(f"Mantenimientos: {count}")
        else:
            print(f"   ⚠️ Error obteniendo mantenimientos: {response.status_code}")
            results["warnings"].append(f"Mantenimientos: Error {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error en mantenimientos: {e}")
        results["errors"].append(f"Mantenimientos: {e}")
    
    # 6. Verificar revisiones
    print("\n6️⃣ Verificando revisiones...")
    try:
        response = requests.get(f"{base_url}/revisiones", timeout=10)
        if response.status_code == 200:
            revisiones = response.json()
            count = len(revisiones)
            print(f"   ✅ {count} revisiones encontradas")
            results["success"].append(f"Revisiones: {count}")
        else:
            print(f"   ⚠️ Error obteniendo revisiones: {response.status_code}")
            results["warnings"].append(f"Revisiones: Error {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error en revisiones: {e}")
        results["errors"].append(f"Revisiones: {e}")
    
    # 7. Verificar RTV
    print("\n7️⃣ Verificando RTV...")
    try:
        response = requests.get(f"{base_url}/rtv", timeout=10)
        if response.status_code == 200:
            rtv = response.json()
            count = len(rtv)
            print(f"   ✅ {count} RTVs encontrados")
            results["success"].append(f"RTVs: {count}")
        else:
            print(f"   ⚠️ Error obteniendo RTVs: {response.status_code}")
            results["warnings"].append(f"RTVs: Error {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error en RTVs: {e}")
        results["errors"].append(f"RTVs: {e}")
    
    # 8. Verificar configuración de alertas
    print("\n8️⃣ Verificando configuración de alertas...")
    try:
        response = requests.get(f"{base_url}/config_alertas", timeout=10)
        if response.status_code == 200:
            config = response.json()
            if config:
                email = config[0].get('email_destino', 'No encontrado')
                print(f"   📧 Email de alertas: {email}")
                if email == "tech@arenalmanoa.com":
                    print("   ✅ Email configurado correctamente")
                    results["success"].append("Email: tech@arenalmanoa.com")
                else:
                    print(f"   ⚠️ Email no es el esperado: {email}")
                    results["warnings"].append(f"Email incorrecto: {email}")
            else:
                print("   ⚠️ No hay configuración de alertas")
                results["warnings"].append("No hay config de alertas")
        else:
            print(f"   ⚠️ Error obteniendo config: {response.status_code}")
            results["warnings"].append(f"Config alertas: Error {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error en config alertas: {e}")
        results["errors"].append(f"Config alertas: {e}")
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 60)
    
    print(f"\n✅ Éxitos: {len(results['success'])}")
    for item in results['success']:
        print(f"   • {item}")
    
    if results['warnings']:
        print(f"\n⚠️ Advertencias: {len(results['warnings'])}")
        for item in results['warnings']:
            print(f"   • {item}")
    
    if results['errors']:
        print(f"\n❌ Errores: {len(results['errors'])}")
        for item in results['errors']:
            print(f"   • {item}")
    
    # Estado general
    print("\n" + "=" * 60)
    if not results['errors'] and len(results['warnings']) <= 2:
        print("🎉 DEPLOYMENT VERIFICADO EXITOSAMENTE")
        print("=" * 60)
        return 0
    elif results['errors']:
        print("❌ DEPLOYMENT CON ERRORES - Revisar logs de Railway")
        print("=" * 60)
        return 1
    else:
        print("⚠️ DEPLOYMENT CON ADVERTENCIAS - Puede requerir atención")
        print("=" * 60)
        return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Error: Debes proporcionar la URL de Railway")
        print("\nUso:")
        print("  python3 verify_deployment.py https://tu-app.railway.app")
        print("\nEjemplo:")
        print("  python3 verify_deployment.py https://sistema-vehicular-production.up.railway.app")
        sys.exit(1)
    
    url = sys.argv[1]
    exit_code = verify_deployment(url)
    sys.exit(exit_code)
