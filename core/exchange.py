import ccxt
import os
import time
from dotenv import load_dotenv
from core.rate_limiter import RateLimiter

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
        
        # Rate limiting
        self.rate_limiter = RateLimiter(max_requests_per_minute=30)
        
        # Market caching (30 minutes)
        self._markets_cache = None
        self._cache_timestamp = 0
        self._cache_duration = int(os.getenv("MARKET_CACHE_MINUTES", "30")) * 60
        
    def _handle_api_call(self, func, *args, **kwargs):
        """
        Wrapper for API calls with rate limiting and 403 error handling.
        """
        # Wait if needed due to rate limits
        self.rate_limiter.wait_if_needed()
        
        try:
            # Record the request
            self.rate_limiter.record_request()
            
            # Make the API call
            result = func(*args, **kwargs)
            
            # Reset 403 counter on success
            self.rate_limiter.reset_403_counter()
            
            return result
            
        except ccxt.RateLimitExceeded as e:
            print(f"⚠️ Rate limit exceeded: {str(e)}")
            self.rate_limiter.record_403_error()
            backoff = self.rate_limiter.get_backoff_time()
            print(f"Waiting {backoff}s before retry...")
            time.sleep(backoff)
            raise
            
        except ccxt.DDoSProtection as e:
            print(f"⚠️ DDoS protection triggered (403): {str(e)}")
            self.rate_limiter.record_403_error()
            backoff = self.rate_limiter.get_backoff_time()
            print(f"Waiting {backoff}s before retry...")
            time.sleep(backoff)
            raise
            
        except Exception as e:
            # Check if it's a 403 error in the message
            if "403" in str(e) or "rate limit" in str(e).lower():
                print(f"⚠️ Possible rate limit error: {str(e)}")
                self.rate_limiter.record_403_error()
                backoff = self.rate_limiter.get_backoff_time()
                print(f"Waiting {backoff}s before retry...")
                time.sleep(backoff)
            raise
        
    def test_connection(self):
        try:
            balance = self._handle_api_call(self.exchange.fetch_balance)
            return True, "[OK] Conexion exitosa a Bitget"
        except Exception as e:
            return False, f"[ERROR] Error de conexion: {str(e)}"
            
    def get_all_symbols(self):
        """
        Obtiene todos los pares USDT perpetuos de Bitget.
        Usa caché de 30 minutos para evitar llamadas innecesarias.
        """
        try:
            now = time.time()
            
            # Check if cache is still valid
            if self._markets_cache and (now - self._cache_timestamp) < self._cache_duration:
                print(f"[CACHE] Usando mercados en cache ({int((now - self._cache_timestamp) / 60)} min)")
                return self._markets_cache
            
            # Load fresh markets
            print("[API] Cargando mercados desde API...")
            self._handle_api_call(self.exchange.load_markets)
            
            symbols = [
                symbol for symbol, market in self.exchange.markets.items() 
                if market['active'] and market['linear'] and market['quote'] == 'USDT'
            ]
            
            # Update cache
            self._markets_cache = symbols
            self._cache_timestamp = now
            
            print(f"[OK] Mercados cargados y cacheados: {len(symbols)} simbolos")
            return symbols
            
        except Exception as e:
            print(f"[ERROR] Error obteniendo simbolos: {e}")
            # Return cached data if available, even if expired
            if self._markets_cache:
                print("[WARN] Usando cache expirado como fallback")
                return self._markets_cache
            return []

    def get_ohlcv(self, symbol, timeframe='15m', limit=100):
        """Obtiene velas del mercado con rate limiting."""
        try:
            return self._handle_api_call(
                self.exchange.fetch_ohlcv, 
                symbol, 
                timeframe=timeframe, 
                limit=limit
            )
        except Exception as e:
            print(f"[ERROR] Error obteniendo OHLCV para {symbol}: {e}")
            return []
            
    def get_ticker(self, symbol):
        """Obtiene el precio actual y volumen de las últimas 24h con rate limiting."""
        try:
            return self._handle_api_call(self.exchange.fetch_ticker, symbol)
        except Exception as e:
            print(f"[ERROR] Error obteniendo ticker para {symbol}: {e}")
            return None

