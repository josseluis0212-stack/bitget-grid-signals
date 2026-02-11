from flask import Flask, render_template, jsonify
import os

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/state')
def get_state():
    from core.state_manager import StateManager
    state = StateManager()
    return jsonify(state.get_state())

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # Solo para desarrollo local
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

