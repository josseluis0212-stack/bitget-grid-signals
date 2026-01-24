import requests
import os
from dotenv import load_dotenv

load_dotenv()

class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_signal(self, symbol, direction, params):
        """Envia un mensaje de alerta formateado para Bitget Grid."""
        emoji = "🚀" if direction == "LONG" else "📉"
        trend_text = "ALCISTA (Compra)" if direction == "LONG" else "BAJISTA (Venta)"
        
        message = (
            f"{emoji} *NUEVA SEÑAL: {symbol}*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Tendencia:* {trend_text}\n"
            f"🛠 *Tipo de Bot:* Future Grid ({direction})\n"
            f"💰 *Precio Entrada:* {params['last_price']}\n\n"
            f"📊 *PARÁMETROS SUGERIDOS*\n"
            f"🔸 *Rango Inferior:* `{params['min']}`\n"
            f"🔸 *Rango Superior:* `{params['max']}`\n"
            f"🔸 *Nro de Grids:* `{params['grids']}`\n"
            f"🔸 *Apalancamiento:* `5x`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Nota:* Abre el bot manualmente en Bitget eligiendo la opción '{direction}'."
        )
        
        self._send(message)

    def send_log(self, message):
        """Envia un log simple del sistema."""
        self._send(f"🤖 *Sistema:* {message}")

    def _send(self, text):
        if not self.token or not self.chat_id:
            print(f"TELEGRAM ERROR: Credenciales faltantes. Msg: {text}")
            return
            
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            requests.post(self.api_url, data=payload)
        except Exception as e:
            print(f"Error enviando a Telegram: {e}")
