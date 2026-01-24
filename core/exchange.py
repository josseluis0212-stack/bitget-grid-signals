import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

class BitgetConnector:
    def __init__(self):
        self.api_key = os.getenv("BITGET_API_KEY")
        self.secret_key = os.getenv("BITGET_SECRET_KEY")
        self.passphrase = os.getenv("BITGET_PASSPHRASE")
        
        self.exchange = ccxt.bitget({
            'apiKey': self.api_key,
            'secret': self.secret_key,
            'password': self.passphrase,
            'options': {
                'defaultType': 'swap', # Futuros Perpetuos
            },
            'enableRateLimit': True,
        })
        
    def test_connection(self):
        try:
            balance = self.exchange.fetch_balance()
            return True, "Conexión exitosa a Bitget"
        except Exception as e:
            return False, f"Error de conexión: {str(e)}"
            
    def get_all_symbols(self):
        """Obtiene todos los pares USDT perpetuos de Bitget."""
        try:
            self.exchange.load_markets()
            symbols = [
                symbol for symbol, market in self.exchange.markets.items() 
                if market['active'] and market['linear'] and market['quote'] == 'USDT'
            ]
            return symbols
        except Exception as e:
            print(f"Error obteniendo símbolos: {e}")
            return []

    def get_ohlcv(self, symbol, timeframe='15m', limit=100):
        """Obtiene velas del mercado."""
        try:
            return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        except Exception as e:
            print(f"Error obteniendo OHLCV para {symbol}: {e}")
            return []
            
    def get_ticker(self, symbol):
        """Obtiene el precio actual y volumen de las últimas 24h."""
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            print(f"Error obteniendo ticker para {symbol}: {e}")
            return None
