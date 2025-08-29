# 🚀 Guía de Deployment - Sistema Vehicular

## 📋 Opciones de Hosting Gratuito

### 🌟 OPCIÓN 1: Cloudflare Pages (RECOMENDADA)
**✅ Ventajas:**
- 100% GRATIS con dominio personalizado
- CDN global ultra-rápido
- SSL automático
- Builds automáticos desde Git
- Bandwidth ilimitado
- 500 builds por mes

**📝 Pasos para Deploy:**

#### 1. Preparar Repositorio
```bash
# Desde tu directorio local
git add .
git commit -m "Deploy: Sistema Vehicular listo para producción"
git push origin main
```

#### 2. Configurar Cloudflare Pages
1. **Ir a**: https://pages.cloudflare.com/
2. **Conectar Git**: Autorizar acceso a tu repositorio GitHub
3. **Configuración del Proyecto**:
   - **Project Name**: `vehicular-system`
   - **Production Branch**: `main`
   - **Build Command**: `./build.sh`
   - **Build Output Directory**: `dist`
   - **Root Directory**: `/`

#### 3. Variables de Entorno
```
ENVIRONMENT=production
API_BASE_URL=tu-backend-url
```

#### 4. Dominio Personalizado
1. **En Cloudflare Pages Dashboard**:
   - Ve a tu proyecto → "Custom domains"
   - Click "Set up a custom domain"
   - Ingresa tu dominio: `tudominio.com`
   - Sigue las instrucciones DNS

### 🔥 OPCIÓN 2: Vercel (Alternativa Excelente)
**✅ Ventajas:**
- Deploy instantáneo
- Preview deploys automáticos
- Analytics incluidos
- Dominio personalizado gratis

**📝 Configuración**:
1. **Ir a**: https://vercel.com/
2. **Import Git Repository**
3. **Configuración**:
   - **Framework**: Other
   - **Build Command**: `./build.sh`
   - **Output Directory**: `dist`

### 🌐 OPCIÓN 3: Netlify
**✅ Ventajas:**
- Drag & drop deployment
- Form handling
- Edge functions

**📝 Configuración**:
1. **Ir a**: https://netlify.com/
2. **Connect to Git** o **Manual Deploy**
3. **Build Settings**:
   - **Build Command**: `./build.sh`
   - **Publish Directory**: `dist`

## 🎯 Configuración de Dominio Personalizado

### 📊 Costo de Dominios (Anual)
- `.com`: $12-15 USD
- `.net`: $13-16 USD
- `.org`: $13-16 USD
- `.app`: $20-25 USD
- `.dev`: $12-15 USD

### 🏪 Registradores Recomendados
1. **Cloudflare Registrar** (más barato)
2. **Namecheap** (popular, buen soporte)
3. **Google Domains** (fácil configuración)
4. **GoDaddy** (conocido mundialmente)

### 🔧 Configuración DNS

#### Para Cloudflare Pages:
```
Tipo: CNAME
Nombre: www
Contenido: tu-proyecto.pages.dev
TTL: Auto

Tipo: A
Nombre: @
Contenido: 192.0.2.1
TTL: Auto
```

#### Para Vercel:
```
Tipo: CNAME
Nombre: www
Contenido: cname.vercel-dns.com
TTL: 3600

Tipo: A
Nombre: @
Contenido: 76.76.19.61
TTL: 3600
```

## 🔐 SSL y Seguridad
- ✅ SSL automático incluido en todas las plataformas
- ✅ Headers de seguridad configurados en `_headers`
- ✅ CSP (Content Security Policy) implementado

## 📈 Monitoreo Post-Deploy
1. **Verificar funcionalidad**: Todas las páginas cargan correctamente
2. **Test de API**: Endpoints responden desde el frontend
3. **Responsive**: Verificar en móviles y tablets
4. **Performance**: Usar Google PageSpeed Insights

## 🆘 Troubleshooting Común

### Error 502 - Bad Gateway
- Verificar URL del backend en configuración
- Comprobar que el backend esté corriendo

### CSS/JS no carga
- Verificar rutas en `_headers` y `_redirects`
- Comprobar estructura de directorios

### CORS Issues
- Configurar headers CORS en el backend
- Verificar dominios permitidos

## 📞 Próximos Pasos
1. ✅ Elegir plataforma de hosting
2. ✅ Registrar dominio personalizado
3. ✅ Configurar DNS
4. ✅ Hacer deploy
5. ✅ Verificar funcionamiento
6. ✅ Configurar monitoreo