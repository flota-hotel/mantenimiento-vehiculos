/*
 * CONFIGURACIÓN EMAIL CON EMAILJS - FRONTEND
 * Solución para evitar bloqueos SMTP en Railway
 */

// 1. CONFIGURACIÓN EMAILJS (Gratuito)
const EMAIL_CONFIG = {
    service: 'emailjs',
    serviceId: 'service_vehicular', // Configurar en emailjs.com
    templateId: 'template_alertas',
    userId: 'tu_user_id' // Public key de EmailJS
};

// 2. FUNCIÓN PARA ENVIAR EMAILS (REEMPLAZA SMTP)
async function sendEmailAlert(alertData) {
    try {
        // Usar EmailJS en lugar de SMTP del backend
        const response = await emailjs.send(
            EMAIL_CONFIG.serviceId,
            EMAIL_CONFIG.templateId,
            {
                to_email: 'contabilidad2@arenalmanoa.com',
                subject: alertData.subject || 'Alerta Sistema Vehicular',
                message: alertData.message,
                fecha: new Date().toLocaleString('es-ES'),
                vehiculos: alertData.vehiculos || '',
                tipo_alerta: alertData.tipo || 'General'
            },
            EMAIL_CONFIG.userId
        );
        
        console.log('✅ Email enviado:', response);
        return { success: true, message: 'Email enviado correctamente' };
        
    } catch (error) {
        console.error('❌ Error enviando email:', error);
        return { success: false, error: error.text || error.message };
    }
}

// 3. INTEGRACIÓN CON EL SISTEMA ACTUAL
function replaceBackendEmail() {
    // Interceptar llamadas al backend de email
    const originalFetch = window.fetch;
    
    window.fetch = async function(url, options) {
        // Si es una llamada de email al backend, usar EmailJS
        if (url.includes('/reportes/enviar-email') || url.includes('/email/test')) {
            console.log('🔄 Interceptando email, usando EmailJS...');
            
            try {
                const body = JSON.parse(options.body || '{}');
                const result = await sendEmailAlert({
                    subject: body.asunto || 'Sistema Vehicular',
                    message: body.contenido || body.message,
                    tipo: 'Reporte'
                });
                
                return new Response(JSON.stringify(result), {
                    status: result.success ? 200 : 500,
                    headers: { 'Content-Type': 'application/json' }
                });
            } catch (e) {
                return new Response(JSON.stringify({
                    success: false, 
                    error: 'Error configurando EmailJS'
                }), { status: 500 });
            }
        }
        
        // Otras llamadas normales
        return originalFetch.apply(this, arguments);
    };
}

// 4. SCRIPT PARA CARGAR EMAILJS
function loadEmailJS() {
    return new Promise((resolve, reject) => {
        if (window.emailjs) {
            resolve();
            return;
        }
        
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/@emailjs/browser@3/dist/email.min.js';
        script.onload = () => {
            emailjs.init(EMAIL_CONFIG.userId);
            resolve();
        };
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

// 5. INICIALIZACIÓN
async function initEmailSystem() {
    try {
        await loadEmailJS();
        replaceBackendEmail();
        console.log('✅ Sistema de email EmailJS inicializado');
    } catch (error) {
        console.error('❌ Error inicializando EmailJS:', error);
    }
}

// Auto-inicializar cuando carga la página
document.addEventListener('DOMContentLoaded', initEmailSystem);

/*
PASOS PARA CONFIGURAR EMAILJS:

1. Ir a: https://www.emailjs.com/
2. Crear cuenta gratuita
3. Crear un service (Gmail/Outlook)
4. Crear template de email
5. Obtener Service ID, Template ID, y Public Key
6. Reemplazar en EMAIL_CONFIG arriba
7. ¡Emails funcionarán desde el frontend!
*/