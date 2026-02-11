import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
api_url = f"https://api.telegram.org/bot{token}/sendMessage"

def send_test_signal():
    message = (
        "🚀 *PRUEBA DE CONEXIÓN: Bitget Trend Sniper*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✅ *Sistema Operativo:* 100%\n"
        "🎯 *Estado:* Escaneando mercado...\n"
        "🛰️ *Nube:* Conectado a Render\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔔 Recibirás una señal real en cuanto se detecte una tendencia fuerte alineada (D/1H/15m)."
    )
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        r = requests.post(api_url, data=payload)
        if r.status_code == 200:
            print("Señal de prueba enviada exitosamente.")
        else:
            print(f"Error enviando señal: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_test_signal()
