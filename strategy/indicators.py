import pandas as pd
import pandas_ta as ta

class Indicators:
    @staticmethod
    def calculate_ema(df, length):
        return ta.ema(df['close'], length=length)

    @staticmethod
    def calculate_atr(df, length=14):
        return ta.atr(df['high'], df['low'], df['close'], length=length)

    @staticmethod
    def calculate_vol_ma(df, length=20):
        return ta.sma(df['volume'], length=length)

    @staticmethod
    def calculate_adx(df, length=14):
        adx = ta.adx(df['high'], df['low'], df['close'], length=length)
        # Rename col for easier access (depends on pandas_ta naming convention)
        return adx[f'ADX_{length}']

    @staticmethod
    def calculate_rsi(df, length=14):
        return ta.rsi(df['close'], length=length)

    @staticmethod
    def calculate_bb(df, length=20, std=2):
        bb = ta.bbands(df['close'], length=length, std=std)
        # Renombrar columnas para facilitar acceso
        return bb.rename(columns={
            f'BBL_{length}_{std}.0': 'bb_lower',
            f'BBM_{length}_{std}.0': 'bb_middle',
            f'BBU_{length}_{std}.0': 'bb_upper'
        })

    @staticmethod
    def klines_to_df(klines):
        """Convierte lista de velas CCXT a DataFrame de Pandas."""
        if not klines: return pd.DataFrame()
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        return df

    @staticmethod
    def add_signals(df):
        """Añade EMA 50, 8, 21 y Vol MA."""
        if df.empty: return df
        df['ema_50'] = Indicators.calculate_ema(df, 50)
        df['ema_fast'] = Indicators.calculate_ema(df, 8)
        df['ema_slow'] = Indicators.calculate_ema(df, 21)
        df['vol_ma'] = Indicators.calculate_vol_ma(df, 20)
        df['atr'] = Indicators.calculate_atr(df)
        df['rsi'] = Indicators.calculate_rsi(df)
        df['adx'] = Indicators.calculate_adx(df)
        
        bb = Indicators.calculate_bb(df)
        df = pd.concat([df, bb], axis=1)
        return df
