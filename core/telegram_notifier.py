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
        """Envia un mensaje de alerta formateado para Bitget Grid (Sniper)."""
        mode = params.get('mode', 'SNIPER')
        emoji = "🎯" if mode == "SNIPER" else "📦"
        type_text = "REVERSIÓN SNIPER" if mode == "SNIPER" else "ZONA CONSOLIDACIÓN"
        dir_text = "LONG (Compra)" if direction == "LONG" else "SHORT (Venta)"
        
        # Parámetros fijos según requerimiento
        margin = "100 USDT"
        leverage = "5x"
        
        message = (
            f"{emoji} *SEÑAL: {type_text}*\n"
            f"💹 *Activo:* {symbol}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔄 *Dirección:* `{dir_text}`\n"
            f"💰 *Precio Actual:* `{params['last_price']}`\n\n"
            f"📊 *CONFIGURACIÓN DEL GRID*\n"
            f"📉 *Límite Inferior:* `{params['min']}`\n"
            f"📈 *Límite Superior:* `{params['max']}`\n"
            f"🔢 *Nro de Grids:* `{params['grids']}`\n"
            f"⚙️ *Apalancamiento:* `{leverage}` (Aislado)\n"
            f"💵 *Margen Sugerido:* `{margin}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✅ *Instrucción:* Abre un 'Future Grid' en Bitget. Elige '{direction}', ingresa los rangos y usa {leverage} con {margin}. Estrategia validada para retorno a la media."
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
