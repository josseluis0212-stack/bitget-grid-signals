"""
Grid Strategy Analyzer - Trend-Following Grid Trading
Basado en principios de: Murphy, Shannon, Wyckoff, Tharp, Elder, Chan
"""

from strategy.indicators import Indicators
from dashboard.app import send_log
import pandas as pd

class GridStrategy:
    def __init__(self, client, config):
        self.client = client
        self.config = config
    
    def analyze_for_grid(self, symbol):
        """
        Analiza si una moneda es candidata para Grid Trading en tendencia.
        Retorna: dict con parámetros del grid o None si no cumple criterios
        """
        
        # 1. ANÁLISIS DIARIO - Tendencia de Fondo (Murphy)
        klines_d = self.client.get_kline(symbol=symbol, interval="D", limit=50)
        if not klines_d:
            return None
            
        df_d = Indicators.klines_to_df(klines_d)
        df_d = Indicators.add_indicators(df_d, self.config)
        last_d = df_d.iloc[-1]
        
        # Tendencia diaria clara
        ema200 = last_d.get('ema_trend', last_d['close'])
        tendencia_alcista_diaria = last_d['close'] > ema200 and last_d['rsi'] > 50
        tendencia_bajista_diaria = last_d['close'] < ema200 and last_d['rsi'] < 50
        
        if not (tendencia_alcista_diaria or tendencia_bajista_diaria):
            return None  # Sin tendencia clara
        
        # 2. ANÁLISIS HORARIO - Confirmación de Fuerza (Shannon - Multi-timeframe)
        klines_1h = self.client.get_kline(symbol=symbol, interval="60", limit=50)
        if not klines_1h:
            return None
            
        df_1h = Indicators.klines_to_df(klines_1h)
        df_1h = Indicators.add_indicators(df_1h, self.config)
        last_1h = df_1h.iloc[-1]
        
        # Filtro ADX - Solo tendencias fuertes (NO RANGO)
        adx_umbral = self.config.get('estrategia', {}).get('adx_umbral', 25)
        if last_1h['adx'] < adx_umbral:
            return None  # Mercado en rango, no apto para grid
        
        # 3. ANÁLISIS 5MIN - Precio Actual y Volatilidad (Elder/Tharp - ATR)
        klines_5m = self.client.get_kline(symbol=symbol, interval="5", limit=100)
        if not klines_5m:
            return None
            
        df_5m = Indicators.klines_to_df(klines_5m)
        df_5m = Indicators.add_indicators(df_5m, self.config)
        last_5m = df_5m.iloc[-1]
        
        precio_actual = float(last_5m['close'])
        atr = float(last_5m['atr'])
        
        # 4. FILTRO DE VOLUMEN - Wyckoff (Acumulación/Distribución)
        volumen_actual = float(last_5m['volume'])
        volumen_promedio = float(last_5m['vol_ma'])
        vol_mult = self.config.get('estrategia', {}).get('volumen_multiplicador', 2.0)
        
        if volumen_actual < (volumen_promedio * vol_mult):
            return None  # Volumen insuficiente
        
        # 5. FILTRO RSI - Evitar extremos
        rsi = float(last_5m['rsi'])
        if tendencia_alcista_diaria:
            rsi_min = self.config.get('estrategia', {}).get('rsi_alcista_min', 50)
            rsi_max = self.config.get('estrategia', {}).get('rsi_alcista_max', 70)
            if not (rsi_min <= rsi <= rsi_max):
                return None
        else:
            rsi_min = self.config.get('estrategia', {}).get('rsi_bajista_min', 30)
            rsi_max = self.config.get('estrategia', {}).get('rsi_bajista_max', 50)
            if not (rsi_min <= rsi <= rsi_max):
                return None
        
        # 6. CÁLCULO DE PARÁMETROS DE GRID (Ernest Chan - Quantitative)
        direccion = "LONG" if tendencia_alcista_diaria else "SHORT"
        
        grid_config = self.config.get('grid', {})
        atr_inf = grid_config.get('atr_inferior_multiplicador', 2)
        atr_sup = grid_config.get('atr_superior_multiplicador', 6)
        
        if direccion == "LONG":
            parametro_inferior = precio_actual - (atr * atr_inf)
            parametro_superior = precio_actual + (atr * atr_sup)
        else:  # SHORT
            parametro_superior = precio_actual + (atr * atr_inf)
            parametro_inferior = precio_actual - (atr * atr_sup)
        
        # 7. NÚMERO DE GRIDS según volatilidad (Kaufman - Adaptive)
        volatilidad_pct = (atr / precio_actual) * 100
        
        if volatilidad_pct < 2:
            num_grids = grid_config.get('grids_volatilidad_baja', 15)
        elif volatilidad_pct < 4:
            num_grids = grid_config.get('grids_volatilidad_media', 10)
        else:
            num_grids = grid_config.get('grids_volatilidad_alta', 7)
        
        # 8. STOP LOSS y TAKE PROFIT (Tharp - Risk Management)
        sl_mult = grid_config.get('sl_atr_multiplicador', 1.0)
        tp_mult = grid_config.get('tp_atr_multiplicador', 2.0)
        
        if direccion == "LONG":
            stop_loss = parametro_inferior - (atr * sl_mult)
            take_profit = parametro_superior + (atr * tp_mult)
        else:
            stop_loss = parametro_superior + (atr * sl_mult)
            take_profit = parametro_inferior - (atr * tp_mult)
        
        # 9. RETORNAR CONFIGURACIÓN COMPLETA
        return {
            "symbol": symbol,
            "direccion": direccion,
            "parametro_inferior": round(parametro_inferior, 4),
            "parametro_superior": round(parametro_superior, 4),
            "precio_actual": round(precio_actual, 4),
            "numero_grids": num_grids,
            "apalancamiento": grid_config.get('apalancamiento', 5),
            "stop_loss": round(stop_loss, 4),
            "take_profit": round(take_profit, 4),
            "duracion_horas": self.config.get('analisis', {}).get('duracion_grid', 24),
            # Confirmaciones
            "adx": round(last_1h['adx'], 1),
            "rsi": round(rsi, 1),
            "volumen_ratio": round(volumen_actual / volumen_promedio, 1),
            "volatilidad_pct": round(volatilidad_pct, 2)
        }
