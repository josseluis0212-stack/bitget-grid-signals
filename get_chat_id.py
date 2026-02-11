import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_TOKEN")
url = f"https://api.telegram.org/bot{token}/getUpdates"

try:
    r = requests.get(url)
    data = r.json()
    
    if data['ok'] and data['result']:
        # Get the most recent chat
        latest_update = data['result'][-1]
        chat_id = latest_update['message']['chat']['id']
        print(f"Tu Chat ID correcto es: {chat_id}")
    else:
        print("No se encontraron mensajes. Asegúrate de haber enviado /start al bot.")
        print(f"Respuesta: {data}")
except Exception as e:
    print(f"Error: {e}")
