#!/usr/bin/env python3
"""
Script de prueba para verificar APIs de ayudas
Prueba cada fuente individualmente y muestra resultados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sources.ayudas_real import AyudasScraperAPIs
from datetime import datetime, timedelta
import json

def print_separator(char="=", length=70):
    print(char * length)

def print_header(text):
    print_separator()
    print(f"  {text}")
    print_separator()

def test_individual_source(scraper, source_name, fetch_method):
    """Prueba una fuente individual"""
    print(f"\n🔍 Probando: {source_name}")
    print("-" * 70)
    
    try:
        ayudas = fetch_method()
        
        if ayudas:
            print(f"✅ ÉXITO: {len(ayudas)} ayudas encontradas")
            
            # Mostrar primera ayuda como ejemplo
            if len(ayudas) > 0:
                print(f"\n📋 Ejemplo de ayuda encontrada:")
                primera = ayudas[0]
                print(f"   Título: {primera['titulo'][:80]}")
                print(f"   Entidad: {primera['entidad']}")
                print(f"   Ámbito: {primera['ambito']}")
                print(f"   URL: {primera['url'][:80]}")
                print(f"   Fuente: {primera.get('fuente', 'N/A')}")
        else:
            print("⚠️  No se encontraron ayudas (puede ser normal)")
        
        return True, len(ayudas)
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False, 0

def main():
    print_header("🧪 TEST DE APIS DE AYUDAS Y SUBVENCIONES")
    
    print("""
Este script prueba cada API individualmente para verificar su funcionamiento.
Las APIs pueden tardar varios segundos en responder.
    """)
    
    # Crear instancia del scraper
    scraper = AyudasScraperAPIs()
    
    # Definir tests
    tests = [
        ("Open Data Euskadi", scraper.fetch_euskadi_opendata),
        ("BDNS - Base Nacional", scraper.fetch_bdns_api),
        ("Bizkaia RSS", scraper.fetch_bizkaia_rss),
        ("SPRI Agencia Vasca", scraper.fetch_spri_rss),
        ("Next Generation EU", scraper.fetch_next_generation),
        ("CDTI", scraper.fetch_cdti_rss),
    ]
    
    # Resultados
    results = {
        'exitosos': 0,
        'fallidos': 0,
        'total_ayudas': 0
    }
    
    # Ejecutar tests
    for nombre, metodo in tests:
        exito, num_ayudas = test_individual_source(scraper, nombre, metodo)
        
        if exito:
            results['exitosos'] += 1
        else:
            results['fallidos'] += 1
        
        results['total_ayudas'] += num_ayudas
        
        # Pausa entre tests
        import time
        time.sleep(2)
    
    # Resumen final
    print("\n")
    print_header("📊 RESUMEN DE PRUEBAS")
    
    print(f"""
    Fuentes probadas:    {len(tests)}
    ✅ Exitosas:         {results['exitosos']}
    ❌ Fallidas:         {results['fallidos']}
    📦 Ayudas totales:   {results['total_ayudas']}
    
    Tasa de éxito: {(results['exitosos']/len(tests)*100):.1f}%
    """)
    
    # Estadísticas del scraper
    stats = scraper.get_statistics()
    print(f"""
    📈 Estadísticas del sistema:
       - Cache: {stats['cache_size']} ayudas únicas
       - Fuentes configuradas: {stats['sources_configured']}
    """)
    
    # Test completo integrado
    print_header("🌍 TEST INTEGRADO - TODAS LAS FUENTES")
    print("\nProbando búsqueda completa en todas las regiones...")
    
    regiones_test = ['euskadi', 'nacional', 'bizkaia']
    
    for region in regiones_test:
        print(f"\n📍 Región: {region.upper()}")
        try:
            ayudas = scraper.get_all_ayudas(region=region)
            print(f"   ✅ {len(ayudas)} ayudas encontradas")
            
            # Mostrar distribución por fuente
            fuentes = {}
            for ayuda in ayudas:
                fuente = ayuda.get('fuente', 'Desconocida')
                fuentes[fuente] = fuentes.get(fuente, 0) + 1
            
            if fuentes:
                print(f"   📊 Distribución por fuente:")
                for fuente, count in sorted(fuentes.items(), key=lambda x: x[1], reverse=True):
                    print(f"      • {fuente}: {count}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Guardar resultados
    print("\n")
    print_header("💾 GUARDANDO RESULTADOS")
    
    try:
        resultados_file = "cache/test_results.json"
        os.makedirs("cache", exist_ok=True)
        
        with open(resultados_file, 'w') as f:
            json.dump({
                'fecha': datetime.now().isoformat(),
                'resultados': results,
                'estadisticas': stats
            }, f, indent=2)
        
        print(f"✅ Resultados guardados en: {resultados_file}")
    
    except Exception as e:
        print(f"⚠️  No se pudieron guardar resultados: {e}")
    
    print("\n")
    print_separator("=")
    print("✨ Test completado")
    print_separator("=")
    
    # Recomendaciones
    if results['fallidos'] > 0:
        print(f"""
⚠️  ATENCIÓN: {results['fallidos']} fuentes fallaron

Posibles causas:
1. Las URLs de las APIs pueden haber cambiado
2. Problemas de conectividad de red
3. Sitios web temporalmente no disponibles
4. Necesidad de actualizar parsers/selectores

Recomendaciones:
- Verifica tu conexión a internet
- Consulta los logs para ver errores específicos
- Algunas fuentes pueden requerir ajustes en el código
        """)
    else:
        print("""
🎉 ¡PERFECTO! Todas las fuentes funcionan correctamente

El sistema está listo para buscar ayudas en:
- Bizkaia, Gipuzkoa, Álava
- Euskadi (Gobierno Vasco)
- Nacional (BDNS)
- Europa (Next Generation)

Comandos disponibles en el chat:
- ayudas buscar
- ayudas region: bizkaia
- ayudas filtrar: tecnología
        """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrumpido por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()