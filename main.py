import eventlet
eventlet.monkey_patch()

import time
import yaml
from core.bybit_client import BybitClient
from core.telegram_bot import TelegramBot
from strategy.grid_strategy import GridStrategy
from dashboard.app import update_ui, send_log, bot_data

def load_config():
    with open("config", "r") as f:
        return yaml.safe_load(f)

def bot_loop():
    config = load_config()
    print("=" * 50)
    print("   🤖 GRID TRADING SIGNAL BOT 🤖")
    print("   Exchange: Bitget USDT Perpetual Futures")
    print("   Mode: Trend-Following Grid Signals")
    print("=" * 50 + "\n")
    
    # Variables de control
    señales_enviadas_hora = []
    ultima_limpieza = time.time()
    
    # Inicializar clientes (MERCADO REAL)
    client = BybitClient(testnet=False, demo=False)
    telegram = TelegramBot()
    grid_strategy = GridStrategy(client, config)
    
    # Mensaje de activación
    telegram.send_message(
        "🤖 *GRID SIGNAL BOT ACTIVADO* 🤖\n\n"
        "📊 *Tipo:* Señales de Grid Trading\n"
        "📡 *Exchange:* Bitget USDT Perpetual\n"
        "🔍 *Estrategia:* Tendencia Fuerte + Alto Volumen\n"
        "📲 *Formato:* Configuración completa de Grid\n\n"
        "✅ *ESCANEANDO MERCADO REAL...*\n"
        "Recibirás señales cuando detecte oportunidades."
    )
    
    try:
        while True:
            if not bot_data["is_running"]:
                time.sleep(5)
                continue

            # Reset contador cada hora
            if time.time() - ultima_limpieza > 3600:
                señales_enviadas_hora = []
                ultima_limpieza = time.time()

            # Recargar config
            config = load_config()
            grid_strategy.config = config
            
            # UI simplificada
            update_ui({
                "balance": "Grid Mode",
                "points": 0,
                "btc_trend": "Autónomo",
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
                
            send_log(f"🔍 ESCANEO GRID: {len(pares)} pares analizando...", "log-success")
            
            max_señales = config.get('analisis', {}).get('max_señales_por_hora', 5)
            escaneados = 0
            
            for par in pares:
                if not bot_data["is_running"]: break
                if len(señales_enviadas_hora) >= max_señales:
                    send_log(f"⏸️ Límite de {max_señales} señales/hora alcanzado", "log-warning")
                    break
                
                escaneados += 1
                
                # ANALIZAR PARA GRID
                grid_params = grid_strategy.analyze_for_grid(par)
                
                if grid_params:
                    # ENVIAR SEÑAL DE GRID
                    send_grid_signal(telegram, grid_params)
                    señales_enviadas_hora.append(time.time())
                    send_log(f"✅ GRID SIGNAL: {par} - {grid_params['direccion']}", "log-success")
                
                if escaneados % 25 == 0:
                    send_log(f"Progreso: {escaneados}/{len(pares)}", "log-info")
                
                time.sleep(0.2)  # Rate limit
                
            intervalo = config.get('analisis', {}).get('escaneo_intervalo', 120)
            send_log(f"✅ Escaneo completo. Siguiente en {intervalo}s", "log-success")
            time.sleep(intervalo)
            
    except KeyboardInterrupt:
        telegram.send_message("⏹️ *Grid Signal Bot Detenido*")
        print("\nBot detenido.")

def send_grid_signal(telegram, params):
    """Envía señal de Grid Trading formateada a Telegram"""
    emoji = "🟢" if params['direccion'] == "LONG" else "🔴"
    
    mensaje = (
        f"{emoji} *SEÑAL DE GRID DETECTADA* {emoji}\n\n"
        f"💎 *Moneda:* {params['symbol']}\n"
        f"📊 *Parámetro Superior:* ${params['parametro_superior']}\n"
        f"📉 *Parámetro Inferior:* ${params['parametro_inferior']}\n"
        f"💰 *Precio Actual:* ${params['precio_actual']}\n"
        f"📍 *Dirección:* {params['direccion']}\n"
        f"⚡ *Apalancamiento:* {params['apalancamiento']}x\n"
        f"🔢 *Número de Grids:* {params['numero_grids']}\n"
        f"🛡️ *Stop Loss:* ${params['stop_loss']}\n"
        f"🎯 *Take Profit:* ${params['take_profit']}\n"
        f"⏱️ *Duración Sugerida:* {params['duracion_horas']} horas\n\n"
        f"✅ *Confirmaciones:*\n"
        f"• ADX: {params['adx']} (Tendencia Fuerte)\n"
        f"• Volumen: {params['volumen_ratio']}x Promedio\n"
        f"• RSI: {params['rsi']}\n"
        f"• Volatilidad: {params['volatilidad_pct']}%\n\n"
        f"⚠️ *Configura este Grid manualmente en Bitget*"
    )
    
    telegram.send_message(mensaje)
    print(f"\n📤 SEÑAL ENVIADA: {params['symbol']} {params['direccion']}")

if __name__ == "__main__":
    eventlet.spawn(bot_loop)
    from dashboard.app import run_server
    print("Iniciando Dashboard...")
    run_server()
