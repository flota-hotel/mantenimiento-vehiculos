#!/bin/bash
# 🚀 Deploy Script - Sistema Vehicular

echo "🚀 DEPLOY SCRIPT - Sistema Vehicular"
echo "=================================="

# Build the project
echo "📦 Building project..."
./build.sh

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📝 Initializing git repository..."
    git init
    git branch -M main
fi

# Add all files
echo "📝 Adding files to git..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "feat: Deploy configuration complete - Sistema Vehicular ready for production"

echo ""
echo "✅ DEPLOY PREPARACIÓN COMPLETA!"
echo ""
echo "📋 PRÓXIMOS PASOS MANUALES:"
echo "1. Push to GitHub: git push origin main"
echo "2. Ir a: https://pages.cloudflare.com/"
echo "3. Conectar repositorio y configurar build"
echo "4. ¡Disfrutar tu sistema en línea!"
echo ""
echo "📁 Archivos listos en dist/ para deploy manual"
echo "📚 Ver GUIA_DOMINIO_PERSONALIZADO.md para instrucciones detalladas"