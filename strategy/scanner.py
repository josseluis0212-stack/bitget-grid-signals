from core.exchange import BitgetConnector
from strategy.indicators import Indicators
import time

class TrendScanner:
    def __init__(self, connector: BitgetConnector):
        self.connector = connector

    def get_trend(self, symbol, timeframe):
        """Determina la tendencia (ALCISTA/BAJISTA/NEUTRAL) basada en EMA 50."""
        klines = self.connector.get_ohlcv(symbol, timeframe, limit=100)
        if not klines: return "NEUTRAL"
        
        df = Indicators.klines_to_df(klines)
        df = Indicators.add_signals(df)
        
        if df.empty or len(df) < 50: return "NEUTRAL"
        
        last = df.iloc[-1]
        if last['close'] > last['ema_50']:
            return "ALCISTA"
        elif last['close'] < last['ema_50']:
            return "BAJISTA"
        return "NEUTRAL"

    def check_triple_alignment(self, symbol):
        """Verifica la triple alineación: Diario, 1H, 15m."""
        trend_d = self.get_trend(symbol, '1d')
        if trend_d == "NEUTRAL": return None
        
        trend_1h = self.get_trend(symbol, '1h')
        if trend_1h != trend_d: return None
        
        # 15m Gatillo y Volumen
        klines_15m = self.connector.get_ohlcv(symbol, '15m', limit=100)
        df = Indicators.klines_to_df(klines_15m)
        df = Indicators.add_signals(df)
        
        if df.empty or len(df) < 50: return None
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Alineación 15m
        trend_15m = "ALCISTA" if last['close'] > last['ema_50'] else "BAJISTA"
        if trend_15m != trend_d: return None
        
        # Gatillo EMA 8/21
        cruce_long = prev['ema_fast'] <= prev['ema_slow'] and last['ema_fast'] > last['ema_slow']
        cruce_short = prev['ema_fast'] >= prev['ema_slow'] and last['ema_fast'] < last['ema_slow']
        
        # Confirmación de Volumen
        vol_ok = last['volume'] > last['vol_ma']
        
        if trend_d == "ALCISTA" and cruce_long and vol_ok:
            return "LONG", self.calculate_grid_params(df, "LONG")
            
        if trend_d == "BAJISTA" and cruce_short and vol_ok:
            return "SHORT", self.calculate_grid_params(df, "SHORT")
            
        return None

    def calculate_grid_params(self, df_15m, direction):
        """Calcula el rango y grids sugeridos."""
        last_price = df_15m.iloc[-1]['close']
        atr = df_15m.iloc[-1]['atr']
        
        # Rango basado en ATR (3x ATR para amplitud de grid)
        range_size = atr * 3.5 
        
        if direction == "LONG":
            min_p = last_price - (range_size * 0.3) # 30% abajo
            max_p = last_price + (range_size * 0.7) # 70% arriba (buscando la tendencia)
        else:
            min_p = last_price - (range_size * 0.7) # 70% abajo
            max_p = last_price + (range_size * 0.3) # 30% arriba
            
        # Asegurar balance
        grid_count = 35 # Valor por defecto seguro para 5x
        
        return {
            "min": round(min_p, 4),
            "max": round(max_p, 4),
            "grids": grid_count,
            "last_price": last_price
        }
