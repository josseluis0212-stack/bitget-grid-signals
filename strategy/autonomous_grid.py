"""
Autonomous Grid Strategy - AI-Powered
Combina: Murphy (tendencia), Wyckoff (volumen), Chan (quant), Tharp (riesgo)
Auto-configura TODO - Sin parámetros del usuario
"""

from strategy.indicators import Indicators
from core.grid_ai import GridAI
from dashboard.app import send_log
import pandas as pd

class AutonomousGridStrategy:
    def __init__(self, client):
        self.client = client
        self.ai = GridAI()
        print("🤖 IA AUTÓNOMA ACTIVADA - Aprendiendo del mercado...")
    
    def analyze_for_grid(self, symbol):
        """
        Análisis completamente autónomo
        La IA decide TODO según su conocimiento y aprendizaje
        """
        
        # Obtener parámetros dinámicos de la IA
        params = self.ai.get_dynamic_params()
        
        # PASO 1: Pre-filtro de liquidez (evitar memecoins sin volumen)
        klines_1h_pre = self.client.get_kline(symbol=symbol, interval="60", limit=10)
        if not klines_1h_pre:
            return None
        
        df_pre = Indicators.klines_to_df(klines_1h_pre)
        vol_avg_1h = df_pre['volume'].mean()
        
        # Filtro mínimo de volumen (evitar coins muertas)
        if vol_avg_1h < 100000:  # Mínimo $100k/hora promedio
            return None
        
        # PASO 2: Análisis Diario - Tendencia de fondo (Murphy - Multi-timeframe)
        klines_d = self.client.get_kline(symbol=symbol, interval="D", limit=100)
        if not klines_d:
            return None
            
        df_d = Indicators.klines_to_df(klines_d)
        df_d = Indicators.add_indicators(df_d, {"estrategia": params})
        last_d = df_d.iloc[-1]
        prev_d = df_d.iloc[-2]
        
        # Identificar tendencia dominante
        ema200_d = last_d.get('ema_trend', last_d['close'])
        rsi_d = last_d['rsi']
        
        # IA: Condiciones estrictas para tendencia
        tendencia_alcista = (
            last_d['close'] > ema200_d and
            prev_d['close'] > prev_d.get('ema_trend', prev_d['close']) and
            rsi_d > 52  # Ligeramente alcista
        )
        
        tendencia_bajista = (
            last_d['close'] < ema200_d and
            prev_d['close'] < prev_d.get('ema_trend', prev_d['close']) and
            rsi_d < 48  # Ligeramente bajista
        )
        
        if not (tendencia_alcista or tendencia_bajista):
            return None  # Sin tendencia clara
        
        # PASO 3: Análisis Horario - Fuerza y Confirmación (Shannon)
        klines_1h = self.client.get_kline(symbol=symbol, interval="60", limit=100)
        if not klines_1h:
            return None
            
        df_1h = Indicators.klines_to_df(klines_1h)
        df_1h = Indicators.add_indicators(df_1h, {"estrategia": params})
        last_1h = df_1h.iloc[-1]
        
        # IA: ADX adaptativo (aprende del historial)
        adx_umbral = params.get("adx_umbral", 25)
        if last_1h['adx'] < adx_umbral:
            return None  # Tendencia débil o rango
        
        # Confirmar alineación de EMAs
        ema8_1h = last_1h.get('ema_fast', last_1h['close'])
        ema21_1h = last_1h.get('ema_slow', last_1h['close'])
        ema200_1h = last_1h.get('ema_trend', last_1h['close'])
        
        if tendencia_alcista:
            if not (ema8_1h > ema21_1h > ema200_1h):
                return None  # Alineación rota
        else:
            if not (ema8_1h < ema21_1h < ema200_1h):
                return None  # Alineación rota
        
        # PASO 4: Análisis 15min - Entrada precisa y Volatilidad
        klines_15m = self.client.get_kline(symbol=symbol, interval="15", limit=100)
        if not klines_15m:
            return None
            
        df_15m = Indicators.klines_to_df(klines_15m)
        df_15m = Indicators.add_indicators(df_15m, {"estrategia": params})
        last_15m = df_15m.iloc[-1]
        
        precio_actual = float(last_15m['close'])
        atr = float(last_15m['atr'])
        
        # IA: Filtro de volatilidad óptima
        volatilidad_pct = (atr / precio_actual) * 100
        min_vol = params.get("min_volatilidad", 1.5)
        max_vol = params.get("max_volatilidad", 8.0)
        
        if not (min_vol <= volatilidad_pct <= max_vol):
            return None  # Muy estable o muy volátil
        
        # PASO 5: Volumen Power - Wyckoff (Smart Money)
        vol_15m = float(last_15m['volume'])
        vol_ma_15m = float(last_15m['vol_ma'])
        vol_mult = params.get("volumen_multiplicador", 2.5)
        
        if vol_15m < (vol_ma_15m * vol_mult):
            return None  # Sin interés institucional
        
        volumen_ratio = vol_15m / vol_ma_15m
        
        # PASO 6: RSI Filter - Evitar sobrecompra/sobreventa extrema
        rsi_15m = float(last_15m['rsi'])
        
        if tendencia_alcista:
            rsi_min = params.get("rsi_alcista_min", 50)
            rsi_max = params.get("rsi_alcista_max", 70)
            if not (rsi_min <= rsi_15m <= rsi_max):
                return None
        else:
            rsi_min = params.get("rsi_bajista_min", 30)
            rsi_max = params.get("rsi_bajista_max", 50)
            if not (rsi_min <= rsi_15m <= rsi_max):
                return None
        
        # PASO 7: Cálculo Autónomo de Grid (Ernest Chan - Quantitative)
        direccion = "LONG" if tendencia_alcista else "SHORT"
        
        # IA: Parámetros adaptativos
        atr_inf = params.get("atr_inferior_multiplicador", 2)
        atr_sup = params.get("atr_superior_multiplicador", 6)
        
        if direccion == "LONG":
            param_inferior = precio_actual - (atr * atr_inf)
            param_superior = precio_actual + (atr * atr_sup)
        else:
            param_superior = precio_actual + (atr * atr_inf)
            param_inferior = precio_actual - (atr * atr_sup)
        
        # IA: Grids adaptativos según volatilidad
        if volatilidad_pct < 2.5:
            num_grids = 12
        elif volatilidad_pct < 4.5:
            num_grids = 9
        else:
            num_grids = 6
        
        # PASO 8: Risk Management (Van Tharp + Alexander Elder)
        if direccion == "LONG":
            stop_loss = param_inferior - (atr * 1.2)
            take_profit = param_superior + (atr * 3.0)
        else:
            stop_loss = param_superior + (atr * 1.2)
            take_profit = param_inferior - (atr * 3.0)
        
        # PASO 9: Retornar configuración
        grid_config = {
            "symbol": symbol,
            "direccion": direccion,
            "parametro_inferior": round(param_inferior, 6),
            "parametro_superior": round(param_superior, 6),
            "precio_actual": round(precio_actual, 6),
            "numero_grids": num_grids,
            "apalancamiento": 5,
            "stop_loss": round(stop_loss, 6),
            "take_profit": round(take_profit, 6),
            "duracion_horas": 24,
            # Métricas para IA
            "adx": round(last_1h['adx'], 1),
            "rsi": round(rsi_15m, 1),
            "volumen_ratio": round(volumen_ratio, 1),
            "volatilidad_pct": round(volatilidad_pct, 2)
        }
        
        # PASO 10: Filtro de Calidad IA
        should_send, quality = self.ai.should_send_signal(grid_config)
        
        if not should_send:
            return None  # Calidad insuficiente
        
        # Registrar para aprendizaje
        grid_config["calidad"] = quality
        self.ai.record_signal(grid_config)
        
        return grid_config
