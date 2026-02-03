"""
Script para forzar una señal de prueba a Telegram
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.telegram_bot import TelegramBot

def send_test_signal():
    telegram = TelegramBot()
    
    # Señal de prueba con formato exacto que el usuario pidió
    mensaje = (
        "🟢 *SEÑAL GRID AI* 🟢\n\n"
        "💎 *Moneda:* SOLUSDT\n"
        "📊 *Parámetro Superior:* $145.50\n"
        "📉 *Parámetro Inferior:* $135.20\n"
        "💰 *Precio Actual:* $138.00\n"
        "📍 *Dirección:* LONG\n"
        "⚡ *Apalancamiento:* 5x\n"
        "🔢 *Número de Grids:* 9\n"
        "🛡️ *Stop Loss:* $133.00\n"
        "🎯 *Take Profit:* $150.00\n"
        "⏱️ *Duración:* 24h\n\n"
        "🤖 *IA Metrics:*\n"
        "• Calidad: EXCELENTE\n"
        "• ADX: 28 (Tendencia)\n"
        "• Vol: 3.2x\n"
        "• RSI: 62\n"
        "• Volatilidad: 3.5%\n\n"
        "⚙️ *Configurar en Bitget manualmente*\n"
        "🔔 **Esta es una señal de PRUEBA**"
    )
    
    telegram.send_message(mensaje)
    print("✅ Señal de prueba enviada a Telegram")

if __name__ == "__main__":
    send_test_signal()
