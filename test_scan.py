"""
Script de prueba para forzar un escaneo manual del mercado
y generar señales de ejemplo sin esperar 5 minutos.
"""
import sys
sys.path.append('.')

from core.exchange import BitgetConnector
from core.telegram_notifier import TelegramNotifier
from strategy.scanner import TrendScanner

def force_scan():
    print("=== ESCANEO MANUAL FORZADO ===\n")
    
    connector = BitgetConnector()
    notifier = TelegramNotifier()
    scanner = TrendScanner(connector)
    
    # Probar conexión
    ok, msg = connector.test_connection()
    print(msg)
    if not ok:
        print("ERROR: No se pudo conectar a Bitget")
        return
    
    # Obtener monedas
    symbols = connector.get_all_symbols()
    print(f"\n📊 Analizando {len(symbols)} monedas...\n")
    
    # Filtro BTC
    btc_trend = scanner.get_trend("BTCUSDT", "1h")
    print(f"🔹 Tendencia BTC (1H): {btc_trend}\n")
    
    signals_found = 0
    
    # Escanear solo las primeras 20 monedas para prueba rápida
    for i, symbol in enumerate(symbols[:20], 1):
        print(f"[{i}/20] Analizando {symbol}...", end=" ")
        
        try:
            signal = scanner.check_triple_alignment(symbol)
            
            if signal:
                direction, params = signal
                
                # Aplicar filtro BTC
                if btc_trend == "BAJISTA" and direction == "LONG":
                    print("❌ Filtrado (BTC bajista, señal LONG)")
                    continue
                if btc_trend == "ALCISTA" and direction == "SHORT":
                    print("❌ Filtrado (BTC alcista, señal SHORT)")
                    continue
                
                print(f"✅ ¡SEÑAL ENCONTRADA!")
                print(f"   Dirección: {direction}")
                print(f"   Rango: {params['min']} - {params['max']}")
                print(f"   Grids: {params['grids']}")
                print(f"   Precio actual: {params['last_price']}")
                
                # Enviar a Telegram
                notifier.send_signal(symbol, direction, params)
                signals_found += 1
            else:
                print("⚪ Sin señal")
                
        except Exception as e:
            print(f"⚠️ Error: {e}")
    
    print(f"\n{'='*50}")
    print(f"✅ Escaneo completado: {signals_found} señales encontradas")
    print(f"{'='*50}")
    
    if signals_found > 0:
        print("\n📱 Revisa tu Telegram para ver las señales enviadas.")
    else:
        print("\n💡 No se encontraron señales en este momento.")
        print("   Esto es normal con filtros estrictos (triple alineación).")

if __name__ == "__main__":
    force_scan()
