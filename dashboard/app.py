from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import os
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Estado global compartido
bot_data = {
    "balance": "AI Grid Mode",
    "points": 0,
    "btc_trend": "Autónomo",
    "is_running": True,
    "positions": [],
    "total_pnl": 0.0,
    "win_count": 0,
    "loss_count": 0,
    "closed_trades": [],
    "signal_history": []
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start')
def start_bot():
    bot_data["is_running"] = True
    return jsonify(status="started")

@app.route('/stop')
def stop_bot():
    bot_data["is_running"] = False
    return jsonify(status="stopped")

@app.route('/signal_history')
def get_signal_history():
    """Retorna historial de señales para el dashboard"""
    history_file = "data/signal_history.json"
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            try:
                history = json.load(f)
                return jsonify(history[:20])  # Últimas 20 señales
            except:
                return jsonify([])
    return jsonify([])

def run_server():
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=False, use_reloader=False)

def start_dashboard():
    thread = threading.Thread(target=run_server)
    thread.daemon = True
    thread.start()
    print("Dashboard iniciado")

def update_ui(data):
    bot_data.update(data)
    socketio.emit('update_data', bot_data)

def send_log(message, type="log-info"):
    socketio.emit('new_log', {"message": message, "type": type})
