import eventlet
eventlet.monkey_patch()

import time
import yaml
from core.bybit_client import BybitClient
from core.telegram_bot import TelegramBot
from strategy.autonomous_grid import AutonomousGridStrategy
from dashboard.app import update_ui, send_log, bot_data

def bot_loop():
    print("=" * 60)
    print("   🧠 GRID AI - SISTEMA AUTÓNOMO INTELIGENTE 🧠")
    print("   Exchange: Bitget USDT Perpetual Futures")
    print("   Modo: Aprendizaje Continuo + Auto-Configuración")
    print("=" * 60 + "\n")
    
    # Contadores
    señales_enviadas_hora = []
    ultima_limpieza = time.time()
    escaneos_totales = 0
    
    # IA AUTÓNOMA - Sin configuración usuario
    client = BybitClient(testnet=False, demo=False)
    telegram = TelegramBot()
    ai_strategy = AutonomousGridStrategy(client)
    
    # Mensaje de activación
    telegram.send_message(
        "🧠 *GRID AI - SISTEMA AUTÓNOMO* 🧠\n\n"
        "🤖 *Modo:* Inteligencia Artificial\n"
        "📊 *Exchange:* Bitget USDT Perpetual\n"
        "🎯 *Estrategia:* Auto-Aprendizaje\n"
        "📈 *Filtros:* Solo Tendencias Fuertes\n"
        "⏱️ *Duración:* Max 24 horas por Grid\n\n"
        "✅ *BOT FUNCIONAL 24/7*\n"
        "Escaneando mercado completo...\n\n"
        "🔔 *Esta es tu señal de prueba*"
    )
    
    print("✅ Señal de prueba enviada a Telegram")
    
    try:
        while True:
            if not bot_data["is_running"]:
                time.sleep(5)
                continue

            # Reset contador horario
            if time.time() - ultima_limpieza > 3600:
                señales_enviadas_hora = []
                ultima_limpieza = time.time()
                print(f"\n📊 Escaneos completados: {escaneos_totales}")

            # UI
            update_ui({
                "balance": "AI Mode",
                "points": ai_strategy.ai.memory.get("signals_history", [])[:1],
                "btc_trend": "Autónomo",
                "positions": [],
                "total_pnl": f"{len(señales_enviadas_hora)}",
                "win_count": 0,
                "loss_count": 0,
                "closed_trades": []
            })
            
            # ESCANEAR MERCADO COMPLETO
            pares = client.get_all_symbols()
            if not pares:
                send_log("❌ Error - Reintentando...", "log-error")
                time.sleep(10)
                continue
                
            send_log(f"🔍 IA analizando {len(pares)} pares...", "log-success")
            print(f"\n🔍 Escaneo #{escaneos_totales + 1} - {len(pares)} pares")
            
            max_señales = 5  # IA: Calidad > Cantidad
            
            for i, par in enumerate(pares):
                if not bot_data["is_running"]: break
                if len(señales_enviadas_hora) >= max_señales:
                    send_log(f"⏸️ Límite diario alcanzado ({max_señales} señales)", "log-warning")
                    break
                
                # IA ANALIZA
                grid_config = ai_strategy.analyze_for_grid(par)
                
                if grid_config:
                    # SEÑAL APROBADA POR IA
                    send_grid_signal(telegram, grid_config)
                    señales_enviadas_hora.append(time.time())
                    send_log(f"✅ SEÑAL IA: {par} ({grid_config.get('calidad', 'N/A')})", "log-success")
                    print(f"📤 SEÑAL: {par} - {grid_config['direccion']} (Calidad: {grid_config.get('calidad', 'N/A')})")
                
                if (i + 1) % 30 == 0:
                    print(f"   Progreso: {i+1}/{len(pares)} ({len(señales_enviadas_hora)} señales)")
                
                time.sleep(0.15)  # Rate limit suave
            
            escaneos_totales += 1
            send_log(f"✅ Escaneo #{escaneos_totales} completo. Próximo en 90s", "log-success")
            print(f"✅ Escaneo completo. Señales: {len(señales_enviadas_hora)}/hora\n")
            time.sleep(90)  # 1.5 min entre escaneos
            
    except KeyboardInterrupt:
        telegram.send_message("⏹️ *Grid AI Detenido*")
        print("\nBot detenido.")

def send_grid_signal(telegram, params):
    """Formato de señal con métricas de IA"""
    emoji = "🟢" if params['direccion'] == "LONG" else "🔴"
    
    mensaje = (
        f"{emoji} *SEÑAL GRID AI* {emoji}\n\n"
        f"💎 *Moneda:* {params['symbol']}\n"
        f"📊 *Parámetro Superior:* ${params['parametro_superior']}\n"
        f"📉 *Parámetro Inferior:* ${params['parametro_inferior']}\n"
        f"💰 *Precio Actual:* ${params['precio_actual']}\n"
        f"📍 *Dirección:* {params['direccion']}\n"
        f"⚡ *Apalancamiento:* {params['apalancamiento']}x\n"
        f"🔢 *Número de Grids:* {params['numero_grids']}\n"
        f"🛡️ *Stop Loss:* ${params['stop_loss']}\n"
        f"🎯 *Take Profit:* ${params['take_profit']}\n"
        f"⏱️ *Duración:* {params['duracion_horas']}h\n\n"
        f"🤖 *IA Metrics:*\n"
        f"• Calidad: {params.get('calidad', 'N/A')}\n"
        f"• ADX: {params['adx']} (Tendencia)\n"
        f"• Vol: {params['volumen_ratio']}x\n"
        f"• RSI: {params['rsi']}\n"
        f"• Volatilidad: {params['volatilidad_pct']}%\n\n"
        f"⚙️ *Configurar en Bitget manualmente*"
    )
    
    telegram.send_message(mensaje)

if __name__ == "__main__":
    eventlet.spawn(bot_loop)
    from dashboard.app import run_server
    print("Dashboard iniciando...")
    run_server()
