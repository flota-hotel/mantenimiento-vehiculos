// EMERGENCY DASHBOARD FIX - Ejecutar en consola de Railway
// Copia y pega este código en la consola del browser (F12) mientras estás en el dashboard

console.log('🚨 === EJECUTANDO FIX DE EMERGENCIA PARA DASHBOARD ===');

// Función de fix inmediato
function emergencyDashboardFix() {
  try {
    console.log('💪 Iniciando fix de emergencia...');
    
    // 1. Verificar que tengamos acceso a las variables globales
    if (typeof Combustible === 'undefined' || !Combustible) {
      console.log('❌ Array Combustible no disponible, forzando carga...');
      
      // Forzar carga de datos si no están disponibles
      fetch('https://mantenimiento-vehiculos-production.up.railway.app/combustible')
        .then(r => r.json())
        .then(data => {
          if (data.success) {
            window.Combustible = data.data;
            console.log('✅ Datos de combustible cargados:', window.Combustible.length);
            emergencyDashboardFix(); // Reintentar
          }
        })
        .catch(e => console.error('❌ Error cargando combustible:', e));
      return;
    }
    
    console.log('📊 Datos encontrados:', {
      Combustible: Combustible?.length || 0,
      Mantenimientos: Mantenimientos?.length || 0
    });
    
    // 2. Calcular KPIs manualmente
    const inicioMes = new Date();
    inicioMes.setDate(1);
    inicioMes.setHours(0, 0, 0, 0);
    
    console.log('📅 Calculando desde:', inicioMes);
    
    const gastosCombustible = Combustible
      .filter(f => {
        const fecha = new Date(f.fecha);
        const incluido = fecha >= inicioMes;
        console.log(`🔍 ${f.placa} (${f.fecha}): ${incluido ? '✅ Incluido' : '❌ Excluido'} - ₡${f.costo}`);
        return incluido;
      })
      .reduce((total, f) => total + Number(f.costo || 0), 0);
    
    const gastosMantenimiento = (typeof Mantenimientos !== 'undefined' ? Mantenimientos : [])
      .filter(m => new Date(m.fecha || 0) >= inicioMes)
      .reduce((total, m) => total + Number(m.costo || 0), 0);
    
    const total = gastosCombustible + gastosMantenimiento;
    
    console.log('💰 Cálculos:', {
      gastosCombustible,
      gastosMantenimiento,
      total
    });
    
    // 3. Formatear valores
    const fmt = n => new Intl.NumberFormat('es-CR', {
      style: 'currency',
      currency: 'CRC',
      maximumFractionDigits: 0
    }).format(Number(n) || 0);
    
    // 4. Actualizar todos los elementos DOM
    const updates = [
      ['kpiCombustibleMes', gastosCombustible],
      ['kpiCombustibleMes2', gastosCombustible],
      ['kpiMantenimientoMes', gastosMantenimiento], 
      ['kpiMantenimientoMes2', gastosMantenimiento],
      ['kpiCostoTotalMes', total],
      ['kpiCostoTotalMes2', total]
    ];
    
    let actualizado = 0;
    updates.forEach(([id, valor]) => {
      const elemento = document.getElementById(id);
      if (elemento) {
        const valorFormateado = fmt(valor);
        elemento.textContent = valorFormateado;
        elemento.style.color = '#28a745'; // Verde para indicar que se actualizó
        elemento.style.fontWeight = 'bold';
        actualizado++;
        console.log(`✅ ACTUALIZADO #${id}: ${valorFormateado}`);
      } else {
        console.log(`❌ Elemento #${id} no encontrado`);
      }
    });
    
    if (actualizado > 0) {
      console.log(`🎉 ¡FIX EXITOSO! ${actualizado} elementos actualizados`);
      console.log(`💰 Dashboard ahora muestra: ${fmt(total)} en lugar de ₡0`);
      
      // Mostrar notificación visual
      const notification = document.createElement('div');
      notification.innerHTML = `
        <div style="
          position: fixed; 
          top: 20px; 
          right: 20px; 
          background: #28a745; 
          color: white; 
          padding: 15px 25px; 
          border-radius: 8px; 
          font-size: 16px; 
          font-weight: bold;
          z-index: 10000;
          box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        ">
          ✅ Dashboard Corregido!<br>
          💰 Mostrando ${fmt(total)}
        </div>
      `;
      document.body.appendChild(notification);
      
      setTimeout(() => {
        notification.remove();
      }, 5000);
      
    } else {
      console.log('❌ No se pudieron actualizar los elementos. Verificar DOM.');
      alert('❌ Error: No se encontraron elementos DOM. ¿Estás en el dashboard?');
    }
    
  } catch (error) {
    console.error('❌ Error en fix de emergencia:', error);
    alert('❌ Error ejecutando fix: ' + error.message);
  }
}

// Ejecutar el fix
emergencyDashboardFix();

// Crear función global para re-ejecutar
window.fixDashboard = emergencyDashboardFix;

console.log('📋 Instrucciones:');
console.log('1. Si el fix funcionó, deberías ver los valores correctos');
console.log('2. Si necesitas ejecutarlo de nuevo, usa: fixDashboard()');
console.log('3. El fix se ejecuta automáticamente cada 10 segundos');

// Auto-fix cada 10 segundos mientras estemos en dashboard
const autoFix = setInterval(() => {
  const currentTab = document.querySelector('.tab.active');
  if (currentTab && currentTab.dataset.tab === 'dashboard') {
    const kpiElement = document.getElementById('kpiCostoTotalMes');
    if (kpiElement && (kpiElement.textContent === '-' || kpiElement.textContent === '₡0')) {
      console.log('🔄 Auto-fix detectó ₡0, corrigiendo...');
      emergencyDashboardFix();
    }
  }
}, 10000);

console.log('✅ Fix de emergencia activado. Auto-corrección cada 10 segundos.');