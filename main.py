import eventlet
eventlet.monkey_patch()

import time
import yaml
from core.bybit_client import BybitClient
from core.telegram_bot import TelegramBot
from strategy.execution_engine import ExecutionEngine
from dashboard.app import update_ui, send_log, bot_data

def load_config():
    with open("config", "r") as f:
        return yaml.safe_load(f)

def bot_loop():
    config = load_config()
    print("========================================")
    print("   BOT DE SEÑALES - MERCADO REAL")
    print("   Exchange: Bitget (Sin ejecución)")
    print("========================================\n")
    
    # Variables de control
    señales_enviadas_hora = []
    ultima_limpieza = time.time()
    
    # Inicializar clientes (SIEMPRE mercado real, sin demo)
    client = BybitClient(testnet=False, demo=False)
    telegram = TelegramBot()
    engine = ExecutionEngine(client, None, None, config, telegram)
    
    # Mensaje de inicio
    telegram.send_message(
        "🎯 *BOT DE SEÑALES ACTIVADO* 🎯\n\n"
        "📊 *Modo:* Solo Señales (NO ejecuta operaciones)\n"
        "📡 *Exchange:* Bitget Mercado Real\n"
        "🔍 *Estrategia:* Triple Pantalla (1D/1H/5m)\n"
        "📲 *Alertas:* Vía Telegram\n\n"
        "✅ Sistema listo. Escaneando mercado..."
    )
    
    try:
        while True:
            if not bot_data["is_running"]:
                time.sleep(5)
                continue

            # Limpiar contador cada hora
            if time.time() - ultima_limpieza > 3600:
                señales_enviadas_hora = []
                ultima_limpieza = time.time()

            # Recargar config
            config = load_config()
            engine.config = config
            
            # UI simplificada
            update_ui({
                "balance": "N/A (Solo Señales)",
                "points": 0,
                "btc_trend": "---",
                "positions": [],
                "total_pnl": "0.00",
                "win_count": 0,
                "loss_count": 0,
                "closed_trades": []
            })
            
            # Obtener pares del mercado REAL
            pares = client.get_all_symbols()
            if not pares:
                send_log("❌ Error obteniendo pares. Reintentando...", "log-error")
                time.sleep(10)
                continue
                
            send_log(f"🔍 ESCANEO: {len(pares)} pares del mercado real", "log-success")
            
            max_señales = config.get('analisis', {}).get('max_señales_por_hora', 10)
            escaneados = 0
            
            for par in pares:
                if not bot_data["is_running"]: break
                if len(señales_enviadas_hora) >= max_señales:
                    send_log(f"⏸️ Límite de {max_señales} señales/hora alcanzado", "log-warning")
                    break
                
                escaneados += 1
                # SOLO DETECTAR - NO EJECUTAR
                signal = engine.check_signal(par)
                
                if signal:
                    engine.send_signal_only(par, signal)
                    señales_enviadas_hora.append(time.time())
                    send_log(f"✅ SEÑAL: {par} - {signal}", "log-success")
                
                if escaneados % 20 == 0:
                    send_log(f"Progreso: {escaneados}/{len(pares)} pares analizados", "log-info")
                
                time.sleep(0.2)  # Rate limit
                
            intervalo = config.get('analisis', {}).get('escaneo_intervalo', 60)
            send_log(f"✅ Escaneo completo. Siguiente en {intervalo}s", "log-success")
            time.sleep(intervalo)
            
    except KeyboardInterrupt:
        telegram.send_message("⏹️ *Bot de Señales Detenido*")
        print("\nBot detenido.")

if __name__ == "__main__":
    eventlet.spawn(bot_loop)
    from dashboard.app import run_server
    print("Iniciando Dashboard...")
    run_server()
