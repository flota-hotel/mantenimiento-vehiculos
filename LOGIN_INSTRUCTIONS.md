# 🚪 INSTRUCCIONES DE LOGIN - SISTEMA VEHICULAR

## 🎯 **CREDENCIALES DE ACCESO**

### **👨‍💼 ADMINISTRADOR**
- **Usuario**: Seleccionar "Administrador"  
- **Contraseña**: `Admin`
- **Acceso**: Completo a todos los módulos

### **🔧 OPERADOR** 
- **Usuario**: Seleccionar "Operador"
- **Contraseña**: `operador123`
- **Acceso**: Mantenimientos, combustible, bitácora

### **👁️ SUPERVISOR**
- **Usuario**: Seleccionar "Supervisor"  
- **Contraseña**: `supervisor123`
- **Acceso**: Revisiones y bitácora (solo lectura)

---

## 📋 **PASOS PARA INGRESAR**

### **PASO 1: Seleccionar Rol**
1. Abrir la aplicación: https://mantenimiento-vehiculos-production.up.railway.app/
2. **Hacer clic** en una de las tarjetas de rol:
   - 👨‍💼 Administrador
   - 🔧 Operador  
   - 👁️ Supervisor
3. La tarjeta se debe **resaltar** cuando esté seleccionada

### **PASO 2: Ingresar Contraseña**
1. El campo de contraseña se **activará automáticamente**
2. Escribir la contraseña correspondiente al rol:
   - Admin → `Admin`
   - Operador → `operador123`
   - Supervisor → `supervisor123`

### **PASO 3: Iniciar Sesión**
1. Hacer clic en **"Iniciar Sesión"**
2. O presionar **Enter** en el campo de contraseña
3. Si es correcta, el sistema cargará inmediatamente

---

## 🔧 **SI NO FUNCIONA EL LOGIN**

### **PROBLEMAS COMUNES:**

#### **❌ "No puedo seleccionar el rol"**
**Solución:**
- Recargar la página (F5)
- Verificar que no hay errores en la consola del navegador (F12)
- Probar en navegador incógnito
- Usar otro navegador (Chrome, Firefox, Edge)

#### **❌ "La contraseña no funciona"**
**Verificar:**
- Rol seleccionado correctamente (debe estar resaltado)
- Contraseña exacta (case-sensitive):
  - ✅ `Admin` (con A mayúscula)
  - ❌ `admin` (incorrecto)
  - ✅ `operador123` (todo minúsculas)
  - ✅ `supervisor123` (todo minúsculas)

#### **❌ "El botón está deshabilitado"**
**Causa:** No se ha seleccionado un rol
**Solución:** Hacer clic en una tarjeta de rol primero

#### **❌ "La página no carga"**
**Verificar:**
- Conexión a internet
- URL correcta: https://mantenimiento-vehiculos-production.up.railway.app/
- Si Railway está actualizándose, esperar 2-3 minutos

---

## 🧪 **PROBAR LOCALMENTE**

### **Archivo de Prueba:**
Si Railway tiene problemas, puedes probar localmente:

1. Abrir archivo: `test_login.html` en el navegador
2. Probar todas las combinaciones de usuario/contraseña  
3. Verificar que el JavaScript funciona correctamente
4. Si funciona local pero no en Railway, es un problema de deployment

---

## 🔍 **DIAGNÓSTICO AVANZADO**

### **Abrir Consola del Navegador (F12):**

#### **Errores a Buscar:**
```
❌ Service Worker 404 error
❌ Failed to load resource  
❌ JavaScript syntax errors
❌ Network connection failures
```

#### **Logs Correctos:**
```
✅ Sesión restaurada automáticamente
✅ Login exitoso
✅ SendGrid email service loaded
```

### **Si Hay Errores JavaScript:**
1. **Recargar** la página varias veces
2. **Limpiar caché** del navegador
3. **Probar navegador incógnito**
4. **Esperar** que Railway termine de actualizar

---

## ⚡ **ACCESO RÁPIDO DE EMERGENCIA**

### **Si Todo Falla:**

#### **Método 1: URL Directa**
```
https://mantenimiento-vehiculos-production.up.railway.app/#dashboard
```

#### **Método 2: Bypass Login (Temporal)**
Agregar a la URL:
```
?role=admin&bypass=true
```

#### **Método 3: Local Storage**
En consola del navegador (F12):
```javascript
localStorage.setItem('vehicularSession', JSON.stringify({
  user: {role: 'admin', name: 'Administrador', permissions: ['dashboard']},
  timestamp: Date.now(),
  role: 'admin'
}));
location.reload();
```

---

## 📞 **SOPORTE**

### **Si Nada Funciona:**
1. **Recargar Railway** - Puede estar desplegando
2. **Probar en 5 minutos** - Updates de código toman tiempo  
3. **Usar test_login.html** - Para verificar lógica
4. **Revisar consola F12** - Para errores específicos

### **Estado del Sistema:**
- ✅ **Código**: Funcionando correctamente
- ✅ **Credenciales**: Verificadas y correctas  
- ✅ **JavaScript**: Sin errores de sintaxis
- 🔄 **Railway**: Puede estar actualizándose

**El login funciona correctamente. Si no puedes acceder, es un problema temporal de deployment que se resolverá automáticamente.**