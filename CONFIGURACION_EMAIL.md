# 📧 GUÍA DE CONFIGURACIÓN DE EMAIL PARA ALERTAS

## 🎯 OBJETIVO
Configurar el sistema para que las alertas lleguen automáticamente a **contabilidad2@arenalmanoa.com**

## ⚡ CONFIGURACIÓN RÁPIDA

### OPCIÓN 1: Gmail / Google Workspace (Recomendado)

#### 1️⃣ Crear Contraseña de Aplicación
1. Ir a [Google Account](https://myaccount.google.com/)
2. Seleccionar **Seguridad** > **Autenticación de 2 factores**
3. Activar autenticación de 2 factores si no está activa
4. Ir a **Contraseñas de aplicación**
5. Generar nueva contraseña para "Sistema Vehicular"
6. **COPIAR** la contraseña generada (16 caracteres)

#### 2️⃣ Configurar en el Sistema
1. Acceder al dashboard como **Administrador**
2. Ir a la sección **"📧 Configuración de Alertas por Email"**
3. Completar los campos:
   - **Email del sistema**: `sistema@arenalmanoa.com` (o el email que use)
   - **Contraseña**: Pegar la contraseña de aplicación generada
   - **Proveedor**: Seleccionar "Gmail / Google Workspace"
   - **Puerto**: Dejar en 587
4. Hacer clic en **"💾 Guardar Configuración"**
5. Hacer clic en **"📧 Probar Email"** para verificar

### OPCIÓN 2: Microsoft Outlook / Office 365

#### 1️⃣ Configurar en el Sistema
1. Acceder al dashboard como **Administrador**
2. Ir a la sección **"📧 Configuración de Alertas por Email"**
3. Completar los campos:
   - **Email del sistema**: Su email de Office 365
   - **Contraseña**: Su contraseña normal de Office 365
   - **Proveedor**: Seleccionar "Outlook / Microsoft 365"
   - **Puerto**: Dejar en 587
4. Hacer clic en **"💾 Guardar Configuración"**
5. Hacer clic en **"📧 Probar Email"** para verificar

### OPCIÓN 3: Servidor de Email Personalizado

#### 1️⃣ Obtener Información del Servidor
Contactar al administrador de IT para obtener:
- Servidor SMTP (ej: `mail.arenalmanoa.com`)
- Puerto SMTP (usualmente 587 o 25)
- Usuario y contraseña del email

#### 2️⃣ Configurar en el Sistema
1. Acceder al dashboard como **Administrador**
2. Ir a la sección **"📧 Configuración de Alertas por Email"**
3. Completar los campos:
   - **Email del sistema**: Email corporativo
   - **Contraseña**: Contraseña del email corporativo
   - **Proveedor**: Seleccionar "Servidor personalizado"
   - **Puerto**: El proporcionado por IT
   - **Servidor SMTP**: El proporcionado por IT
4. Hacer clic en **"💾 Guardar Configuración"**
5. Hacer clic en **"📧 Probar Email"** para verificar

## 🔧 CONFIGURACIÓN VÍA API (Para Técnicos)

### Configurar Gmail
```bash
curl -X POST http://localhost:8000/config/email \
  -H "Content-Type: application/json" \
  -d '{
    "sender_email": "sistema@arenalmanoa.com",
    "sender_password": "CONTRASEÑA_DE_APLICACION_16_CARACTERES",
    "provider": "gmail"
  }'
```

### Configurar Outlook
```bash
curl -X POST http://localhost:8000/config/email \
  -H "Content-Type: application/json" \
  -d '{
    "sender_email": "sistema@arenalmanoa.com",
    "sender_password": "contraseña_office365",
    "provider": "outlook"
  }'
```

### Configurar Servidor Personalizado
```bash
curl -X POST http://localhost:8000/config/email \
  -H "Content-Type: application/json" \
  -d '{
    "sender_email": "sistema@arenalmanoa.com",
    "sender_password": "contraseña_corporativa",
    "provider": "custom",
    "smtp_server": "mail.arenalmanoa.com",
    "smtp_port": 587
  }'
```

## 🧪 PROBAR CONFIGURACIÓN

### Desde el Dashboard
1. Hacer clic en **"📧 Probar Email"**
2. Verificar que llegue el email de prueba a contabilidad2@arenalmanoa.com

### Desde API
```bash
curl -X POST http://localhost:8000/config/email/test
```

### Verificar Alertas Completas
```bash
curl http://localhost:8000/alertas/verificar
```

## 🚨 TIPOS DE ALERTAS QUE RECIBIRÁ

Una vez configurado, recibirá emails automáticos para:

### 🔧 **Mantenimientos**
- Cambios de aceite próximos (por fecha o kilometraje)
- Mantenimiento preventivo programado

### 🛡️ **Pólizas de Seguro**
- Pólizas que vencen en 30 días o menos
- Alertas críticas para pólizas que vencen en 7 días

### 🔍 **RTV (Revisión Técnica)**
- RTV que vencen en 30 días o menos
- Alertas críticas para RTV que vencen en 7 días

### ⚠️ **Fallas en Revisiones**
- Vehículos que no aprobaron revisiones recientes
- Problemas específicos: motor, frenos, luces, llantas, carrocería

### ⛽ **Consumo Anormal de Combustible**
- Vehículos con eficiencia 25% menor al promedio histórico
- Alertas de posibles problemas mecánicos o mal uso

## 📊 FRECUENCIA DE ALERTAS

- **Manual**: Usando el botón "🔍 Verificar Alertas" en el dashboard
- **Automático**: Se puede configurar con cron jobs del sistema

## ❓ SOLUCIÓN DE PROBLEMAS

### "Password authentication is not supported"
- **Gmail**: Necesita contraseña de aplicación, no la contraseña normal
- **Outlook**: Verificar que la cuenta tenga SMTP habilitado

### "SMTP connection failed"
- Verificar servidor y puerto SMTP
- Verificar conectividad de red
- Contactar al administrador de IT

### "Email sent but not received"
- Verificar carpeta de SPAM/Correo no deseado
- Verificar que contabilidad2@arenalmanoa.com sea correcto
- Verificar filtros de email corporativo

## 📞 SOPORTE TÉCNICO

Para problemas de configuración:
1. Verificar los logs del sistema en `/home/user/webapp/api.log`
2. Contactar al administrador de IT de Arenal Manoa
3. Verificar configuración de firewall y puertos SMTP

## ✅ VERIFICACIÓN FINAL

Email configurado correctamente cuando:
- ✅ Estado muestra "✅ Configurado" en el dashboard
- ✅ Email de prueba llega a contabilidad2@arenalmanoa.com
- ✅ Verificación de alertas retorna alertas procesadas
- ✅ No hay errores en los logs del sistema

---
**Sistema de Gestión Vehicular - Hotel Arenal Manoa**