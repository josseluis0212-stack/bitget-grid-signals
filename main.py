import time
from core.exchange import BitgetConnector
from core.telegram_notifier import TelegramNotifier
from strategy.scanner import TrendScanner
from dashboard.app import start_health_check
import os

def main():
    start_health_check()
    print("--- INICIANDO BITGET TREND SNIPER v1.0 ---")
    
    connector = BitgetConnector()
    notifier = TelegramNotifier()
    scanner = TrendScanner(connector)
    
    # 1. Probar conexión
    ok, msg = connector.test_connection()
    print(msg)
    if not ok:
        print("ERROR: Verifica tus llaves en el archivo .env")
        return

    notifier.send_log("Bot iniciado exitosamente. Escaneando mercado 24/7...")
    
    # Cache para no repetir señales muy seguido
    last_signals = {} # symbol -> timestamp

    while True:
        try:
            # Obtener todas las monedas
            symbols = connector.get_all_symbols()
            print(f"Analizando {len(symbols)} monedas en Bitget...")
            
            # Filtro Bitcoin
            btc_trend = scanner.get_trend("BTCUSDT", "1h")
            print(f"Tendencia BTC (1H): {btc_trend}")
            
            for symbol in symbols:
                # Evitar señales repetidas (max 1 vez cada 4 horas por moneda)
                now = time.time()
                if symbol in last_signals and (now - last_signals[symbol]) < 14400:
                    continue
                
                # Regla: La moneda debe seguir a BTC si BTC es fuerte
                if btc_trend != "NEUTRAL":
                    # Solo escaneamos la moneda si coincide con la dirección de BTC
                    # para maximizar probabilidad.
                    pass 

                signal = scanner.check_triple_alignment(symbol)
                
                if signal:
                    direction, params = signal
                    
                    # Filtro final: Si BTC está bajista, no mandar Longs.
                    if btc_trend == "BAJISTA" and direction == "LONG": continue
                    if btc_trend == "ALCISTA" and direction == "SHORT": continue
                    
                    print(f"🚀 ¡SEÑAL ENCONTRADA! {symbol} - {direction}")
                    notifier.send_signal(symbol, direction, params)
                    last_signals[symbol] = now
                
                time.sleep(1) # Delay para evitar ban de API
                
            print("Escaneo completado. Esperando 5 minutos...")
            time.sleep(300)
            
        except Exception as e:
            print(f"Error en el bucle principal: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
