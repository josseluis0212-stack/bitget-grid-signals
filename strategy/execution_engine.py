from strategy.indicators import Indicators
from strategy.trend_analyzer import TrendAnalyzer
from dashboard.app import send_log
import pandas as pd
import time

class ExecutionEngine:
    def __init__(self, client, risk_manager, memory_manager, config, telegram_bot):
        self.client = client
        self.risk_manager = risk_manager
        self.memory_manager = memory_manager
        self.config = config
        self.telegram = telegram_bot
        self.trend_analyzer = TrendAnalyzer(client, config)

    def check_signal(self, symbol):
        # 1. FILTRO MACRO (DIARIO - 1D) 🌊
        klines_d = self.client.get_kline(symbol=symbol, interval="D", limit=100)
        if not klines_d: return None
        df_d = Indicators.klines_to_df(klines_d)
        df_d = Indicators.add_indicators(df_d, self.config)
        last_d = df_d.iloc[-1]
        
        # Tendencia Diaria: Precio > EMA200
        ema200_d = last_d.get('ema_trend', 0)
        tendencia_diaria_alcista = last_d['close'] > ema200_d and last_d['rsi'] > 50
        tendencia_diaria_bajista = last_d['close'] < ema200_d and last_d['rsi'] < 50
        
        # 2. FILTRO TÁCTICO (1 HORA - 1H) 💪
        klines_1h = self.client.get_kline(symbol=symbol, interval="60", limit=50)
        if not klines_1h: return None
        df_1h = Indicators.klines_to_df(klines_1h)
        df_1h = Indicators.add_indicators(df_1h, self.config)
        last_1h = df_1h.iloc[-1]
        
        # Fuerza H1: ADX > 15 (Más flexible)
        if last_1h['adx'] <= 15: return None 

        alineacion_1h_alcista = last_1h['close'] > last_1h['ema_slow']
        alineacion_1h_bajista = last_1h['close'] < last_1h['ema_slow']
        
        # 3. GATILLO MICRO (5 MIN - 5m) 🔫
        klines_5m = self.client.get_kline(symbol=symbol, interval="5", limit=100)
        if not klines_5m: return None
        df_5m = Indicators.klines_to_df(klines_5m)
        df_5m = Indicators.add_indicators(df_5m, self.config)
        
        last_5m = df_5m.iloc[-1]
        prev_5m = df_5m.iloc[-2]
        
        # Cruce EMAs 8/21
        cruce_buy = prev_5m['ema_fast'] <= prev_5m['ema_slow'] and last_5m['ema_fast'] > last_5m['ema_slow']
        cruce_sell = prev_5m['ema_fast'] >= prev_5m['ema_slow'] and last_5m['ema_fast'] < last_5m['ema_slow']
        
        # Volumen Power (> Promedio)
        vol_power = last_5m['volume'] > last_5m['vol_ma']
        
        if not vol_power: return None

        # --- EVALUACIÓN FINAL ---
        if cruce_buy and tendencia_diaria_alcista and alineacion_1h_alcista:
            return "Buy"
            
        if cruce_sell and tendencia_diaria_bajista and alineacion_1h_bajista:
            return "Sell"
            
        return None



    def execute_trade(self, symbol):
        # 1. ESTRATEGIA PRINCIPAL (TRIPLE PANTALLA)
        # Verificar Límite de 5 Operaciones
        posiciones = self.client.get_active_positions()
        if len(posiciones) >= self.config['trading']['max_operaciones_simultaneas']:
            return 

        if any(p['symbol'] == symbol for p in posiciones): return

        # Buscar señal PRINCIPAL
        signal = self.check_signal(symbol)
        if not signal: return
            
        send_log(f"¡Señal TRIPLE ALINEACIÓN en {symbol}: {signal}!", "log-success")
        
        # Guardar señal en historial
        self.save_signal_to_history(symbol, signal)
        
        self.telegram.send_message(
            f"🏛️ *SEÑAL INSTITUCIONAL*\n\n"
            f"💎 *Moneda:* {symbol}\n"
            f"🚀 *Dirección:* {signal}\n"
            f"✅ Diario: Tendencia OK\n"
            f"✅ 1 Hora: ADX > 15 (Activo)\n"
            f"✅ 5 Min: Cruce + Volumen"
        )
        
        # Ejecución
        balance = self.client.get_balance()
        monto = self.config['trading']['monto_por_operacion'] 
        
        # IA Scoring
        if self.memory_manager.get_coin_score(symbol) < self.config['ia']['umbral_aprendizaje']: 
            monto *= 0.5 

        # Datos para SL/TP
        klines = self.client.get_kline(symbol=symbol, interval="5", limit=20)
        df_calc = Indicators.klines_to_df(klines)
        df_calc = Indicators.add_indicators(df_calc, self.config)
        entry = float(df_calc.iloc[-1]['close'])
        atr = float(df_calc.iloc[-1]['atr'])
        
        # Stops
        sl_dist = atr * self.config['riesgo']['stop_loss_atr_multiplicador']
        sl = entry - sl_dist if signal == "Buy" else entry + sl_dist
        
        # TP Infinito
        tp_ratio = self.config['riesgo']['take_profit_ratio']
        tp_dist = atr * 10 if tp_ratio == 0 else atr * tp_ratio
        tp = entry + tp_dist if signal == "Buy" else entry - tp_dist
        
        # Cantidad
        qty = round(monto / entry, 3) 
        
        # Enviar orden
        self.client.place_order(symbol, signal, "Market", qty, sl=sl, tp=tp)
        msg_final = f"✅ *Orden Ejecutada (5x)*\n{symbol} {signal}\nSL: {sl:.4f}"
        self.telegram.send_message(msg_final)

    def save_signal_to_history(self, symbol, direction):
        """Guarda la señal en un archivo JSON para el historial del dashboard."""
        import json
        import os
        from datetime import datetime
        
        history_file = "data/signal_history.json"
        
        # Crear directorio si no existe
        os.makedirs("data", exist_ok=True)
        
        # Cargar historial existente
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                try:
                    history = json.load(f)
                except:
                    history = []
        else:
            history = []
        
        # Agregar nueva señal
        signal_entry = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "direction": direction,
            "time": time.strftime("%H:%M:%S")
        }
        
        history.insert(0, signal_entry)
        
        # Limitar a últimas 100 señales
        if len(history) > 100:
            history = history[:100]
        
        # Guardar
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)

    def send_signal_only(self, symbol, direction):
        """Envía una señal detallada a Telegram SIN ejecutar ninguna operación."""
        # Obtener datos para calcular SL/TP sugeridos
        klines = self.client.get_kline(symbol=symbol, interval="5", limit=20)
        if not klines:
            return
            
        df = Indicators.klines_to_df(klines)
        df = Indicators.add_indicators(df, self.config)
        
        last_candle = df.iloc[-1]
        entry = float(last_candle['close'])
        atr = float(last_candle.get('atr', entry * 0.02))  # 2% fallback
        
        # Calcular SL y TP sugeridos
        sl_mult = self.config.get('riesgo', {}).get('stop_loss_atr_multiplicador', 2.0)
        tp_ratio = self.config.get('riesgo', {}).get('take_profit_ratio', 3.0)
        apal = self.config.get('riesgo', {}).get('apalancamiento_sugerido', 5)
        
        if direction == "Buy":
            sl = entry - (atr * sl_mult)
            tp = entry + (atr * sl_mult * tp_ratio)
            emoji = "🟢"
        else:
            sl = entry + (atr * sl_mult)
            tp = entry - (atr * sl_mult * tp_ratio)
            emoji = "🔴"
        
        # Calcular % de riesgo/beneficio
        risk_pct = abs((entry - sl) / entry) * 100
        reward_pct = abs((tp - entry) / entry) * 100
        
        # Mensaje detallado para Telegram
        mensaje = (
            f"{emoji} *SEÑAL DETECTADA* {emoji}\n\n"
            f"💎 *Moneda:* {symbol}\n"
            f"📍 *Dirección:* {direction.upper()}\n"
            f"💰 *Precio Entrada:* ${entry:.4f}\n\n"
            f"🛡️ *Stop Loss:* ${sl:.4f} ({risk_pct:.2f}%)\n"
            f"🎯 *Take Profit:* ${tp:.4f} ({reward_pct:.2f}%)\n"
            f"⚡ *Apalancamiento Sugerido:* {apal}x\n"
            f"📊 *Ratio R:R:* 1:{tp_ratio}\n\n"
            f"✅ *Confirmaciones:*\n"
            f"• Diario (1D): Tendencia Alineada\n"
            f"• 1 Hora (1H): ADX > 15 (Activo)\n"
            f"• 5 Minutos (5m): Cruce EMA + Volumen\n\n"
            f"⚠️ *IMPORTANTE:* Esta es solo una alerta.\n"
            f"Abre la operación manualmente en Bitget."
        )
        
        self.telegram.send_message(mensaje)
        self.save_signal_to_history(symbol, direction)
        
        send_log(f"📤 Señal enviada: {symbol} {direction}", "log-success")

