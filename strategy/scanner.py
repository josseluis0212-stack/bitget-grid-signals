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
        
        # Filtro de tendencia opcional para asegurar que no vamos contra tendencia fuerte
        if last['close'] > last['ema_50']:
            return "ALCISTA"
        elif last['close'] < last['ema_50']:
            return "BAJISTA"
        return "NEUTRAL"

    def check_rebound(self, symbol):
        """
        Estrategia Sniper Reversion:
        Fase 1: Detección de Extremos (1H)
        Fase 2: Confirmación de Rebote / Ruptura de Estructura (15m)
        """
        # 1. Fase 1: Análisis de 1H para Extremos
        klines_1h = self.connector.get_ohlcv(symbol, '1h', limit=100)
        df_1h = Indicators.klines_to_df(klines_1h)
        df_1h = Indicators.add_signals(df_1h)
        
        if df_1h.empty or len(df_1h) < 30: return None
        
        last_1h = df_1h.iloc[-1]
        
        # Filtros de Fase 1 (Al menos 2 de 3)
        long_conds = [
            last_1h['rsi'] < 30,
            last_1h['close'] <= last_1h['bb_lower'],
            last_1h['volume'] > last_1h['vol_ma'] * 1.5
        ]
        
        short_conds = [
            last_1h['rsi'] > 70,
            last_1h['close'] >= last_1h['bb_upper'],
            last_1h['volume'] > last_1h['vol_ma'] * 1.5
        ]
        
        potential_direction = None
        if sum(long_conds) >= 2:
            potential_direction = "LONG"
        elif sum(short_conds) >= 2:
            potential_direction = "SHORT"
            
        if not potential_direction: return None
        
        # 2. Fase 2: Confirmación en 15m (Ruptura de Estructura)
        klines_15m = self.connector.get_ohlcv(symbol, '15m', limit=50)
        df_15m = Indicators.klines_to_df(klines_15m)
        df_15m = Indicators.add_signals(df_15m)
        
        if df_15m.empty or len(df_15m) < 10: return None
        
        last_15m = df_15m.iloc[-1]
        # Buscar el ultimo swing high/low para confirmar ruptura
        if potential_direction == "LONG":
            # Ruptura del máximo de las últimas 5 velas de 15m
            recent_max = df_15m.iloc[-6:-1]['high'].max()
            if last_15m['close'] > recent_max:
                return "LONG", self.calculate_grid_params(symbol, df_15m, "LONG")
        else:
            # Ruptura del mínimo de las últimas 5 velas de 15m
            recent_min = df_15m.iloc[-6:-1]['low'].min()
            if last_15m['close'] < recent_min:
                return "SHORT", self.calculate_grid_params(symbol, df_15m, "SHORT")
        
        return None

    def check_triple_alignment(self, symbol):
        """Metodo de compatibilidad - ahora usa rebote."""
        return self.check_rebound(symbol)

    def calculate_grid_params(self, symbol, df_ref, direction):
        """Calcula el rango y grids sugeridos con precision dinamica."""
        last = df_ref.iloc[-1]
        last_price = last['close']
        
        # Obtener ADX para ver si estamos en rango o tendencia
        adx = last.get('adx', 25)
        
        # Precision del simbolo
        precision = 4
        markets = self.connector.exchange.markets
        if symbol in markets:
            precision = markets[symbol]['precision']['price']
        
        if adx < 20:
            # Escenario Consolidación: Rango más ancho
            min_p = last_price * 0.94
            max_p = last_price * 1.06
            grid_count = 100
            mode = "CONSOLIDACION"
        else:
            # Escenario Reversión (Sniper): Rango ajustado
            if direction == "LONG":
                min_p = last_price * 0.985
                max_p = last_price * 1.05
            else:
                min_p = last_price * 0.95
                max_p = last_price * 1.015
            grid_count = 50
            mode = "SNIPER"
            
        return {
            "min": round(min_p, precision),
            "max": round(max_p, precision),
            "grids": grid_count,
            "last_price": last_price,
            "mode": mode
        }
