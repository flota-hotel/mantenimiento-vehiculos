# 🚀 GUÍA DE DEPLOYMENT MANUAL - Cloudflare Pages

## ✅ TOKEN VERIFICADO
Tu token de Cloudflare está **ACTIVO y VÁLIDO**:
- **Account ID**: `e3f61cc1b17d25d4dbd6fa9cfb5c86e9`
- **Token**: Funcional para verificación

## 📋 SITUACIÓN ACTUAL
El token actual tiene permisos limitados. Para deployment completo necesitas un token con permisos de **Cloudflare Pages:Edit**. 

## 🎯 OPCIÓN 1: DEPLOYMENT MANUAL (MÁS RÁPIDO)

### 📁 ARCHIVOS LISTOS
Tu proyecto está **100% preparado** para deployment:
```
✅ dist/ - Carpeta con archivos de producción
✅ _headers - Headers de seguridad configurados  
✅ _redirects - Routing para SPA
✅ index.html - Aplicación optimizada
✅ static/ - Assets estáticos
```

### 🔥 PASOS PARA DEPLOYMENT MANUAL:

#### 1. **Abrir Cloudflare Pages Dashboard**
   - Ve a: https://dash.cloudflare.com/e3f61cc1b17d25d4dbd6fa9cfb5c86e9/pages
   - Login con tu cuenta

#### 2. **Crear Nuevo Proyecto**
   - Click "Create a project"
   - Seleccionar "Upload assets"
   - **Nombre del proyecto**: `sistema-vehicular`

#### 3. **Upload de Archivos**
   - **ARRASTRAR**: toda la carpeta `dist/` desde tu computadora
   - O **ZIP** la carpeta dist/ y subir el archivo
   - Click "Deploy site"

#### 4. **¡LISTO!** 
   Tu app estará disponible en:
   ```
   https://sistema-vehicular.pages.dev
   ```

## 🎯 OPCIÓN 2: CREAR TOKEN CON PERMISOS COMPLETOS

### 🔧 Crear Nuevo Token API:
1. **Ir a**: https://dash.cloudflare.com/e3f61cc1b17d25d4dbd6fa9cfb5c86e9/api-tokens
2. **Click**: "Create Token" → "Custom token"
3. **Permisos necesarios**:
   ```
   Cloudflare Pages:Edit
   Account:Read
   Zone:Read (si usarás dominio personalizado)
   ```
4. **Account Resources**: Include - tu cuenta
5. **Zone Resources**: Include - All zones (si tienes dominio)

### 🚀 Deployment Automático con Nuevo Token:
```bash
# Con el nuevo token:
export CLOUDFLARE_API_TOKEN=tu_nuevo_token
npx wrangler pages deploy dist --project-name sistema-vehicular
```

## 🎯 OPCIÓN 3: DEPLOYMENT DESDE GIT (RECOMENDADO LARGO PLAZO)

### 🔗 Conectar Repositorio:
1. **En Cloudflare Pages Dashboard**:
   - "Create a project" → "Connect to Git"
   - Autorizar GitHub
   - Seleccionar tu repositorio

2. **Configuración de Build**:
   ```
   Project Name: sistema-vehicular
   Production Branch: main
   Framework Preset: None
   Build Command: ./build.sh
   Build Output Directory: dist
   Root Directory: (leave blank)
   ```

3. **Variables de Entorno** (si necesitas):
   ```
   ENVIRONMENT=production
   ```

## 🌐 CONFIGURAR DOMINIO PERSONALIZADO

### Después del deployment:
1. **En tu proyecto de Pages**:
   - Tab "Custom domains"
   - "Set up a custom domain"
   - Ingresar tu dominio

2. **Configurar DNS**:
   - Si el dominio está en Cloudflare: **Automático**
   - Si está en otro proveedor: Agregar CNAME

## 📊 VENTAJAS DE CADA OPCIÓN

### 🔥 Manual Upload (Más Rápido):
- ✅ **Inmediato** (5 minutos)
- ✅ **No requiere Git**
- ✅ **Funciona ahora mismo**
- ❌ No hay deploy automático

### 🔄 Git Integration (Mejor a largo plazo):
- ✅ **Deploy automático** en cada push
- ✅ **Preview branches**
- ✅ **Rollback fácil**
- ✅ **CI/CD completo**

## 💰 COSTO TOTAL
- **Cloudflare Pages**: **GRATIS**
- **Bandwidth**: **Ilimitado**
- **SSL**: **Incluido**
- **Dominio personalizado**: ~$12/año

## 🆘 SIGUIENTE PASO RECOMENDADO

**Para publicar TU SISTEMA HOY MISMO**:

1. **Descargar** la carpeta `dist/` a tu computadora
2. **Ir a**: https://dash.cloudflare.com/e3f61cc1b17d25d4dbd6fa9cfb5c86e9/pages
3. **Create project** → "Upload assets"
4. **Arrastrar** carpeta `dist/`
5. **¡Deploy!**

### 📱 Tu sistema estará en línea en: 
```
🌐 https://sistema-vehicular.pages.dev
```

**¡En menos de 5 minutos tu Sistema Vehicular estará accesible mundialmente!** 🎉