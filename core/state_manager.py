"""
State Manager - Mantiene el estado del bot para el dashboard
"""
from datetime import datetime
from threading import Lock

class StateManager:
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.btc_price = 0.0
        self.btc_trend = "NEUTRAL"
        self.btc_change_24h = 0.0
        self.current_scanning = ""
        self.scan_progress = {"current": 0, "total": 0}
        self.last_update = datetime.now()
        self.signals_today = []
        self.total_scanned = 0
        self.bot_start_time = datetime.now()
        self.is_scanning = False
        
    def update_btc(self, price, trend, change_24h=0.0):
        with self._lock:
            self.btc_price = price
            self.btc_trend = trend
            self.btc_change_24h = change_24h
            self.last_update = datetime.now()
    
    def update_scan_progress(self, current, total, symbol=""):
        with self._lock:
            self.current_scanning = symbol
            self.scan_progress = {"current": current, "total": total}
            self.is_scanning = True
            self.last_update = datetime.now()
    
    def add_signal(self, symbol, direction, params):
        with self._lock:
            signal = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "direction": direction,
                "params": params
            }
            self.signals_today.append(signal)
            # Mantener solo las últimas 10
            if len(self.signals_today) > 10:
                self.signals_today = self.signals_today[-10:]
    
    def finish_scan(self):
        with self._lock:
            self.is_scanning = False
            self.current_scanning = ""
            self.total_scanned += self.scan_progress["total"]
    
    def get_state(self):
        with self._lock:
            uptime_seconds = (datetime.now() - self.bot_start_time).total_seconds()
            uptime_hours = uptime_seconds / 3600
            
            return {
                "btc": {
                    "price": round(self.btc_price, 2),
                    "trend": self.btc_trend,
                    "change_24h": round(self.btc_change_24h, 2)
                },
                "scanning": {
                    "is_active": self.is_scanning,
                    "current_symbol": self.current_scanning,
                    "progress": self.scan_progress
                },
                "signals": {
                    "recent": self.signals_today[-5:],  # Últimas 5
                    "total_today": len(self.signals_today),
                    "long_count": sum(1 for s in self.signals_today if s["direction"] == "LONG"),
                    "short_count": sum(1 for s in self.signals_today if s["direction"] == "SHORT")
                },
                "stats": {
                    "total_scanned": self.total_scanned,
                    "uptime_hours": round(uptime_hours, 1),
                    "last_update": self.last_update.isoformat()
                }
            }
