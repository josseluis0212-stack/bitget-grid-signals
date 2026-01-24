from flask import Flask
import os
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bitget Trend Sniper is Operational 🚀"

def run():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

def start_health_check():
    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()
