#!/bin/bash

# Script auxiliar para deployment en Railway
# Este script ayuda a verificar y preparar el deployment

echo "============================================================"
echo "🚂 RAILWAY DEPLOYMENT HELPER"
echo "============================================================"
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Error: main.py no encontrado. Ejecuta este script desde el directorio del proyecto.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Directorio correcto detectado${NC}"
echo ""

# Verificar base de datos
if [ -f "vehicular_system.db" ]; then
    echo -e "${GREEN}✅ Base de datos encontrada${NC}"
    
    # Contar registros
    echo ""
    echo "📊 Contando registros en la base de datos..."
    python3 << 'EOF'
import sqlite3
try:
    conn = sqlite3.connect('vehicular_system.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM vehiculos")
    vehiculos = cursor.fetchone()[0]
    print(f"   • Vehículos: {vehiculos}")
    
    cursor.execute("SELECT COUNT(*) FROM bitacora")
    bitacora = cursor.fetchone()[0]
    print(f"   • Bitácora: {bitacora}")
    
    cursor.execute("SELECT COUNT(*) FROM combustible")
    combustible = cursor.fetchone()[0]
    print(f"   • Combustible: {combustible}")
    
    cursor.execute("SELECT email_destino FROM config_alertas WHERE activo = 1 LIMIT 1")
    result = cursor.fetchone()
    if result:
        print(f"   • Email alertas: {result[0]}")
    
    conn.close()
except Exception as e:
    print(f"   ❌ Error verificando base de datos: {e}")
EOF
else
    echo -e "${YELLOW}⚠️ Base de datos no encontrada. Se creará en Railway.${NC}"
fi

echo ""
echo "============================================================"
echo "📝 CHECKLIST PRE-DEPLOYMENT"
echo "============================================================"
echo ""

# Verificar archivos necesarios
echo "Verificando archivos necesarios..."
files_ok=true

if [ -f "requirements.txt" ]; then
    echo -e "${GREEN}✅ requirements.txt${NC}"
else
    echo -e "${RED}❌ requirements.txt no encontrado${NC}"
    files_ok=false
fi

if [ -f "Procfile" ]; then
    echo -e "${GREEN}✅ Procfile${NC}"
else
    echo -e "${RED}❌ Procfile no encontrado${NC}"
    files_ok=false
fi

if [ -f "railway.toml" ]; then
    echo -e "${GREEN}✅ railway.toml${NC}"
else
    echo -e "${RED}❌ railway.toml no encontrado${NC}"
    files_ok=false
fi

if [ -f "runtime.txt" ]; then
    echo -e "${GREEN}✅ runtime.txt${NC}"
else
    echo -e "${YELLOW}⚠️ runtime.txt no encontrado (opcional)${NC}"
fi

echo ""

if [ "$files_ok" = true ]; then
    echo -e "${GREEN}✅ Todos los archivos necesarios están presentes${NC}"
else
    echo -e "${RED}❌ Faltan archivos necesarios. Revisa la configuración.${NC}"
    exit 1
fi

echo ""
echo "============================================================"
echo "🚀 OPCIONES DE DEPLOYMENT"
echo "============================================================"
echo ""
echo "Opción 1: Merge Pull Request (Recomendado)"
echo "  1. Ve a: https://github.com/flota-hotel/mantenimiento-vehiculos/pull/2"
echo "  2. Click en 'Merge pull request'"
echo "  3. Railway desplegará automáticamente"
echo ""
echo "Opción 2: Railway CLI"
echo "  Si tienes Railway CLI instalado:"
echo "  $ railway up"
echo ""
echo "Opción 3: Railway Dashboard"
echo "  1. Ve a: https://railway.app"
echo "  2. Selecciona tu proyecto"
echo "  3. Click en 'Deploy' o 'Redeploy'"
echo ""

echo "============================================================"
echo "⚠️ IMPORTANTE: PERSISTENCIA DE DATOS"
echo "============================================================"
echo ""
echo -e "${YELLOW}Railway usa almacenamiento efímero por defecto.${NC}"
echo ""
echo "Para persistir los datos, tienes dos opciones:"
echo ""
echo "Opción A: Volume Persistente"
echo "  1. En Railway Dashboard, ve a Settings"
echo "  2. Agrega un Volume"
echo "  3. Mount path: /app/vehicular_system.db"
echo ""
echo "Opción B: PostgreSQL (Recomendado)"
echo "  1. Agrega servicio PostgreSQL en Railway"
echo "  2. Railway configurará las variables automáticamente"
echo "  3. Actualiza el código para usar PostgreSQL"
echo ""

echo "============================================================"
echo "🔍 VERIFICACIÓN POST-DEPLOYMENT"
echo "============================================================"
echo ""
echo "Una vez desplegado, verifica con:"
echo "  $ python3 verify_deployment.py https://tu-app.railway.app"
echo ""
echo "O verifica manualmente:"
echo "  • Abre tu app en Railway"
echo "  • Verifica que veas los vehículos"
echo "  • Verifica que el email sea tech@arenalmanoa.com"
echo ""

echo "============================================================"
echo "📚 DOCUMENTACIÓN ADICIONAL"
echo "============================================================"
echo ""
echo "Para más información, consulta:"
echo "  • DATOS_CARGADOS.md - Guía completa de deployment"
echo "  • RESUMEN_FINAL.md - Resumen de cambios"
echo ""

echo "============================================================"
echo -e "${GREEN}✅ Listo para deployment${NC}"
echo "============================================================"
echo ""
