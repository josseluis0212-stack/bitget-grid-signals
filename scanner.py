import time
from core.exchange import BitgetConnector
from core.telegram_notifier import TelegramNotifier
from strategy.scanner import TrendScanner
from core.state_manager import StateManager
import os
import sys

def run_scanner():
    """Funcion principal del scanner de mercado"""
    print("--- INICIANDO BITGET TREND SNIPER v1.0 ---")
    
    connector = BitgetConnector()
    notifier = TelegramNotifier()
    scanner = TrendScanner(connector)
    state = StateManager()
    
    # Configuracion de rate limiting desde .env
    SYMBOL_DELAY = int(os.getenv("SYMBOL_DELAY_SECONDS", "3"))  # 3s por defecto
    SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL_SECONDS", "600"))  # 10 min por defecto
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))  # Pausa cada 50 simbolos
    BATCH_PAUSE = int(os.getenv("BATCH_PAUSE_SECONDS", "30"))  # 30s de pausa
    
    # 1. Probar conexion
    ok, msg = connector.test_connection()
    print(msg)
    if not ok:
        print("ERROR: Verifica tus llaves en el archivo .env")
        return

    notifier.send_log("[OK] Bot iniciado exitosamente. Escaneando mercado 24/7...")
    
    # Cache para no repetir senales muy seguido
    last_signals = {} # symbol -> timestamp

    while True:
        try:
            # Obtener todas las monedas (ahora con cache de 30 min)
            symbols = connector.get_all_symbols()
            print(f"\n[SCAN] Analizando {len(symbols)} monedas en Bitget...")
            print(f"[CONFIG] {SYMBOL_DELAY}s/simbolo, pausa cada {BATCH_SIZE} simbolos\n")
            
            # Filtro Bitcoin
            btc_trend = scanner.get_trend("BTCUSDT", "1h")
            print(f"[BTC] Tendencia BTC (1H): {btc_trend}")
            
            # Obtener precio BTC para el dashboard
            btc_klines = connector.get_ohlcv("BTCUSDT", "1h", limit=24)
            if btc_klines:
                btc_price = btc_klines[-1][4]  # Close price
                btc_price_24h_ago = btc_klines[0][4]
                btc_change = ((btc_price - btc_price_24h_ago) / btc_price_24h_ago) * 100
                state.update_btc(btc_price, btc_trend, btc_change)
            
            signals_found = 0
            
            for i, symbol in enumerate(symbols, 1):
                # Actualizar progreso del escaneo
                state.update_scan_progress(i, len(symbols), symbol)
                
                # Evitar senales repetidas (max 1 vez cada 4 horas por moneda)
                now = time.time()
                if symbol in last_signals and (now - last_signals[symbol]) < 14400:
                    continue
                
                # Regla: La moneda debe seguir a BTC si BTC es fuerte
                if btc_trend != "NEUTRAL":
                    # Solo escaneamos la moneda si coincide con la direccion de BTC
                    # para maximizar probabilidad.
                    pass 

                signal = scanner.check_triple_alignment(symbol)
                
                if signal:
                    direction, params = signal
                    
                    # Filtro final: Si BTC esta bajista, no mandar Longs.
                    if btc_trend == "BAJISTA" and direction == "LONG": continue
                    if btc_trend == "ALCISTA" and direction == "SHORT": continue
                    
                    print(f"[SIGNAL] SENAL ENCONTRADA! {symbol} - {direction}")
                    notifier.send_signal(symbol, direction, params)
                    state.add_signal(symbol, direction, params)
                    last_signals[symbol] = now
                    signals_found += 1
                
                # Delay entre simbolos (3-5 segundos para evitar rate limit)
                time.sleep(SYMBOL_DELAY)
                
                # Batch processing: pausa cada N simbolos
                if i % BATCH_SIZE == 0 and i < len(symbols):
                    print(f"\n[BATCH] Pausa de batch ({i}/{len(symbols)}) - esperando {BATCH_PAUSE}s...\n")
                    time.sleep(BATCH_PAUSE)
            
            state.finish_scan()
            print(f"\n[OK] Escaneo completado. Senales encontradas: {signals_found}")
            print(f"[WAIT] Esperando {SCAN_INTERVAL // 60} minutos hasta el proximo escaneo...\n")
            time.sleep(SCAN_INTERVAL)
            
        except Exception as e:
            print(f"[ERROR] Error en el bucle principal: {e}")
            print("[WAIT] Esperando 60s antes de reintentar...")
            time.sleep(60)

if __name__ == "__main__":
    # Ejecutar scanner en modo standalone
    run_scanner()
