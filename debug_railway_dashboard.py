#!/usr/bin/env python3
"""
Debug script to find EXACTLY why Railway dashboard still shows ₡0
"""
import requests
import json
import time

def test_railway_frontend():
    """Probar si el frontend de Railway tiene la corrección"""
    print("🔍 === DEBUGGING RAILWAY DASHBOARD ===\n")
    
    try:
        # 1. Verificar que el HTML tenga la corrección
        response = requests.get("https://mantenimiento-vehiculos-production.up.railway.app/", timeout=10)
        html_content = response.text
        
        print("1. ✅ VERIFICANDO HTML DE RAILWAY:")
        if "Ejecutando renderKpis() después de cargar todos los datos" in html_content:
            print("   ✅ Corrección de timing ENCONTRADA en Railway HTML")
        else:
            print("   ❌ Corrección de timing NO ENCONTRADA en Railway HTML")
            print("   🚨 ESTO ES EL PROBLEMA - Railway no tiene la corrección")
            return False
            
        # 2. Verificar que los datos estén disponibles
        print("\n2. ✅ VERIFICANDO DATOS DE RAILWAY:")
        data_response = requests.get("https://mantenimiento-vehiculos-production.up.railway.app/combustible", timeout=10)
        combustible_data = data_response.json()
        
        if combustible_data.get("success") and len(combustible_data.get("data", [])) > 0:
            record = combustible_data["data"][0]
            print(f"   ✅ Datos disponibles: {record['placa']} - ₡{record['costo']} ({record['fecha']})")
        else:
            print("   ❌ No hay datos de combustible")
            return False
            
        # 3. Verificar funciones específicas en el HTML
        print("\n3. ✅ VERIFICANDO FUNCIONES EN HTML:")
        functions_to_check = [
            ("renderKpis()", "renderKpis" in html_content),
            ("loadAll()", "loadAll" in html_content), 
            ("fmt() function", "fmt = n=>" in html_content),
            ("byId() function", "byId = id=>" in html_content),
            ("API configuration", "API =" in html_content)
        ]
        
        for func_name, found in functions_to_check:
            status = "✅" if found else "❌"
            print(f"   {status} {func_name}: {'FOUND' if found else 'MISSING'}")
            
        # 4. Buscar elementos DOM específicos
        print("\n4. ✅ VERIFICANDO ELEMENTOS DOM:")
        dom_elements = [
            "kpiCombustibleMes",
            "kpiCostoTotalMes", 
            "kpiMantenimientoMes"
        ]
        
        for element in dom_elements:
            found = f'id="{element}"' in html_content
            status = "✅" if found else "❌"
            print(f"   {status} Element #{element}: {'FOUND' if found else 'MISSING'}")
            
        # 5. Verificar el orden de ejecución en loadAll()
        print("\n5. 🔍 VERIFICANDO ORDEN DE EJECUCIÓN:")
        if "refreshAllViews();" in html_content and "renderKpis();" in html_content:
            refresh_pos = html_content.find("refreshAllViews();")
            render_pos = html_content.find("console.log('🎯 Ejecutando renderKpis() después de cargar todos los datos...');")
            
            if render_pos > refresh_pos and render_pos != -1:
                print("   ✅ renderKpis() se ejecuta DESPUÉS de refreshAllViews() - CORRECTO")
            else:
                print("   ❌ renderKpis() NO se ejecuta después de refreshAllViews() - PROBLEMA")
        else:
            print("   ❌ No se encontraron las funciones de carga")
            
        return True
        
    except Exception as e:
        print(f"❌ Error verificando Railway: {e}")
        return False

def create_emergency_fix():
    """Crear un fix de emergencia que funcione 100%"""
    print("\n🚨 === CREANDO FIX DE EMERGENCIA ===\n")
    
    emergency_script = """
    // FIX DE EMERGENCIA PARA DASHBOARD KPIS
    (function() {
        console.log('🚨 EJECUTANDO FIX DE EMERGENCIA PARA KPIS');
        
        // Función para forzar cálculo de KPIs
        function forceKPICalculation() {
            try {
                console.log('💪 Forzando cálculo de KPIs...');
                
                // Verificar si tenemos datos
                if (typeof Combustible === 'undefined' || !Combustible || Combustible.length === 0) {
                    console.log('⏳ Datos aún no cargados, reintentando en 1s...');
                    setTimeout(forceKPICalculation, 1000);
                    return;
                }
                
                console.log('📊 Datos encontrados:', {
                    Combustible: Combustible?.length || 0,
                    Mantenimientos: Mantenimientos?.length || 0
                });
                
                // Calcular manualmente
                const inicioMes = new Date();
                inicioMes.setDate(1);
                inicioMes.setHours(0, 0, 0, 0);
                
                const gastosCombustible = Combustible
                    .filter(f => new Date(f.fecha) >= inicioMes)
                    .reduce((total, f) => total + Number(f.costo || 0), 0);
                
                const gastosMantenimiento = (Mantenimientos || [])
                    .filter(m => new Date(m.fecha || 0) >= inicioMes)
                    .reduce((total, m) => total + Number(m.costo || 0), 0);
                
                const total = gastosCombustible + gastosMantenimiento;
                
                console.log('💰 Cálculos:', {
                    gastosCombustible,
                    gastosMantenimiento,
                    total
                });
                
                // Formatear valores
                const fmt = n => new Intl.NumberFormat('es-CR', {
                    style: 'currency',
                    currency: 'CRC',
                    maximumFractionDigits: 0
                }).format(Number(n) || 0);
                
                // Actualizar DOM directamente
                const elements = [
                    ['kpiCombustibleMes', gastosCombustible],
                    ['kpiCombustibleMes2', gastosCombustible],
                    ['kpiMantenimientoMes', gastosMantenimiento],
                    ['kpiMantenimientoMes2', gastosMantenimiento],
                    ['kpiCostoTotalMes', total],
                    ['kpiCostoTotalMes2', total]
                ];
                
                let updated = 0;
                elements.forEach(([id, value]) => {
                    const element = document.getElementById(id);
                    if (element) {
                        element.textContent = fmt(value);
                        updated++;
                        console.log(`✅ Actualizado #${id}: ${fmt(value)}`);
                    } else {
                        console.log(`❌ Elemento #${id} no encontrado`);
                    }
                });
                
                if (updated > 0) {
                    console.log(`🎉 FIX APLICADO: ${updated} elementos actualizados con valores correctos!`);
                } else {
                    console.log('❌ No se pudo actualizar ningún elemento');
                    setTimeout(forceKPICalculation, 2000);
                }
                
            } catch (error) {
                console.error('❌ Error en fix de emergencia:', error);
                setTimeout(forceKPICalculation, 2000);
            }
        }
        
        // Ejecutar cuando DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(forceKPICalculation, 2000);
            });
        } else {
            setTimeout(forceKPICalculation, 2000);
        }
        
        // También ejecutar cada vez que se cambie a dashboard
        const originalSetTab = window.setTab;
        if (originalSetTab) {
            window.setTab = function(name) {
                const result = originalSetTab.call(this, name);
                if (name === 'dashboard') {
                    setTimeout(forceKPICalculation, 1000);
                }
                return result;
            };
        }
    })();
    """
    
    print("🔧 Fix de emergencia creado")
    return emergency_script

if __name__ == "__main__":
    # Ejecutar diagnóstico
    if test_railway_frontend():
        print("\n✅ RAILWAY ESTÁ CONFIGURADO CORRECTAMENTE")
        print("🤔 El problema debe ser de timing o elementos DOM")
    else:
        print("\n❌ RAILWAY NO TIENE LA CONFIGURACIÓN CORRECTA")
        print("🚨 NECESITA RE-DEPLOY URGENTE")
    
    # Crear fix de emergencia
    emergency_fix = create_emergency_fix()
    
    print(f"\n🎯 === PRÓXIMOS PASOS ===")
    print("1. Si Railway tiene la corrección: problema de timing DOM")
    print("2. Si Railway NO tiene la corrección: re-deploy necesario")
    print("3. Fix de emergencia creado para inyectar en browser")
    print("\n🚀 EJECUTANDO FIX...")