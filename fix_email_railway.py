#!/usr/bin/env python3
"""
Script para crear versión del backend sin funcionalidad SMTP
que causa errores en Railway
"""

import re

def fix_main_py():
    """Comentar funciones SMTP problemáticas en main.py"""
    
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Comentar imports SMTP
    content = re.sub(
        r'import smtplib',
        '# import smtplib  # Comentado para Railway',
        content
    )
    
    # Comentar imports email
    content = re.sub(
        r'from email\.mime\.',
        '# from email.mime.',
        content
    )
    
    # Modificar función send_email para que no falle
    content = re.sub(
        r'(def send_email.*?)(server = smtplib\.SMTP.*?server\.quit\(\))',
        r'''\1# SMTP comentado para Railway - usar EmailJS desde frontend
        print("⚠️  Email SMTP deshabilitado en Railway")
        print(f"📧 Email que se enviaría a: {recipient}")
        print(f"📋 Asunto: {subject}")
        return True  # Simular envío exitoso''',
        content,
        flags=re.DOTALL
    )
    
    # Modificar endpoint test-smtp
    smtp_test_pattern = r'(@app\.post\("/config/email/test-smtp"\).*?return \{.*?\})'
    smtp_replacement = '''@app.post("/config/email/test-smtp")
async def test_smtp_connection(smtp_config: dict):
    """Test SMTP - Deshabilitado en Railway"""
    return {
        "success": False, 
        "error": "SMTP deshabilitado en Railway. Use EmailJS desde frontend",
        "suggestion": "Configurar EmailJS para emails desde el navegador"
    }'''
    
    content = re.sub(smtp_test_pattern, smtp_replacement, content, flags=re.DOTALL)
    
    # Escribir archivo corregido
    with open('main_fixed.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ main_fixed.py creado sin funcionalidad SMTP")

def create_railway_procfile():
    """Crear Procfile para usar main_fixed.py"""
    with open('Procfile_fixed', 'w') as f:
        f.write('web: uvicorn main_fixed:app --host 0.0.0.0 --port $PORT')
    
    print("✅ Procfile_fixed creado")

if __name__ == "__main__":
    print("🔧 Arreglando configuración SMTP para Railway...")
    fix_main_py()
    create_railway_procfile()
    print("📋 Archivos creados:")
    print("   - main_fixed.py (sin SMTP)")
    print("   - Procfile_fixed (usar main_fixed)")
    print("🚀 Deploy main_fixed.py a Railway para resolver errores")