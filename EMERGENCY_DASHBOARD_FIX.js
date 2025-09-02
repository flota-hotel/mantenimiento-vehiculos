// 🚨 EJECUTAR EN CONSOLA DEL NAVEGADOR (F12) PARA FIX INMEDIATO
// Copio y pega este código completo en la consola y presiona Enter

console.log('🚨 === INICIANDO FIX DE EMERGENCIA DEL DASHBOARD ===');

// Función para formatear moneda
function fmt(n) {
    return new Intl.NumberFormat('es-CR', {
        style: 'currency',
        currency: 'CRC',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(n);
}

// Fix inmediato de KPIs
function emergencyKPIFix() {
    try {
        console.log('💪 === CALCULANDO KPIs MANUALMENTE ===');
        
        // Obtener fecha inicio del mes
        const inicioMes = new Date();
        inicioMes.setDate(1);
        inicioMes.setHours(0, 0, 0, 0);
        
        // Calcular gastos de combustible del mes actual
        let gastosCombustibleMes = 0;
        if (window.Combustible && Array.isArray(window.Combustible)) {
            gastosCombustibleMes = window.Combustible
                .filter(f => new Date(f.fecha) >= inicioMes)
                .reduce((total, f) => total + Number(f.costo || 0), 0);
        }
        
        console.log('🔥 Gastos combustible mes:', gastosCombustibleMes);
        
        // Actualizar elementos del DOM directamente
        const updates = [
            ['kpiCombustibleMes', gastosCombustibleMes],
            ['kpiCostoTotalMes', gastosCombustibleMes],
            ['kpiVehiculosActivos', window.Vehiculos ? window.Vehiculos.length : 0],
            ['kpiMantenimientosMes', window.Mantenimientos ? window.Mantenimientos.filter(m => new Date(m.fecha) >= inicioMes).length : 0]
        ];
        
        updates.forEach(([elementId, valor]) => {
            const elemento = document.getElementById(elementId);
            if (elemento) {
                const valorFormateado = elementId.includes('Combustible') || elementId.includes('Costo') ? 
                    fmt(valor) : valor.toString();
                elemento.textContent = valorFormateado;
                elemento.style.color = '#28a745';
                elemento.style.fontWeight = 'bold';
                console.log(`✅ Actualizado ${elementId}: ${valorFormateado}`);
            } else {
                console.warn(`⚠️ No encontrado elemento: ${elementId}`);
            }
        });
        
        console.log('🎉 === FIX DE EMERGENCIA COMPLETADO ===');
        return true;
        
    } catch (error) {
        console.error('❌ Error en fix de emergencia:', error);
        return false;
    }
}

// Ejecutar fix inmediatamente
emergencyKPIFix();

// Configurar actualización automática cada 5 segundos
setInterval(emergencyKPIFix, 5000);

console.log('🎯 Fix aplicado! Los KPIs deberían mostrar valores correctos ahora.');
console.log('💡 Si aún ves ceros, ejecuta: emergencyKPIFix()');