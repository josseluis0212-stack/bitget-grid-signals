"""
AI Learning System for Grid Trading Signals
Auto-ajusta parámetros basado en éxito de señales
Inspired by: Marcos López de Prado - Advances in Financial Machine Learning
"""

import json
import os
from datetime import datetime, timedelta

class GridAI:
    def __init__(self):
        self.memory_file = "data/ai_memory.json"
        self.memory = self.load_memory()
    
    def load_memory(self):
        """Carga memoria de señales pasadas"""
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as f:
                return json.load(f)
        return {
            "signals_history": [],
            "coin_scores": {},  # Symbol -> score (0-100)
            "strategy_params": {
                "adx_umbral": 25,
                "volumen_multiplicador": 2.5,
                "rsi_alcista_min": 50,
                "rsi_alcista_max": 70,
                "rsi_bajista_min": 30,
                "rsi_bajista_max": 50,
                "atr_inferior_multiplicador": 2,
                "atr_superior_multiplicador": 6,
                "min_volatilidad": 1.5,  # %
                "max_volatilidad": 8.0   # %
            }
        }
    
    def save_memory(self):
        """Guarda memoria a disco"""
        with open(self.memory_file, "w") as f:
            json.dump(self.memory, f, indent=2)
    
    def get_coin_score(self, symbol):
        """Obtiene score de una moneda (0-100)"""
        return self.memory["coin_scores"].get(symbol, 50)  # Default: neutral
    
    def update_coin_score(self, symbol, success):
        """Actualiza score basado en resultado"""
        current_score = self.get_coin_score(symbol)
        
        if success:
            new_score = min(100, current_score + 10)
        else:
            new_score = max(0, current_score - 15)
        
        self.memory["coin_scores"][symbol] = new_score
        self.save_memory()
    
    def record_signal(self, grid_params):
        """Registra señal para aprendizaje futuro"""
        signal_record = {
            "timestamp": datetime.now().isoformat(),
            "symbol": grid_params["symbol"],
            "direccion": grid_params["direccion"],
            "adx": grid_params["adx"],
            "rsi": grid_params["rsi"],
            "volumen_ratio": grid_params["volumen_ratio"],
            "volatilidad": grid_params["volatilidad_pct"],
            "score": self.get_coin_score(grid_params["symbol"])
        }
        
        self.memory["signals_history"].insert(0, signal_record)
        
        # Mantener solo últimas 200 señales
        if len(self.memory["signals_history"]) > 200:
            self.memory["signals_history"] = self.memory["signals_history"][:200]
        
        self.save_memory()
    
    def get_dynamic_params(self):
        """Retorna parámetros auto-ajustados basados en aprendizaje"""
        return self.memory["strategy_params"]
    
    def calculate_signal_quality(self, grid_params):
        """
        Calcula calidad de señal (0-100)
        Basado en múltiples factores ponderados
        """
        score = 0
        
        # 1. Tendencia (ADX) - peso 30%
        adx = grid_params.get("adx", 0)
        if adx >= 30:
            score += 30
        elif adx >= 25:
            score += 20
        elif adx >= 20:
            score += 10
        
        # 2. Volumen (Wyckoff) - peso 25%
        vol_ratio = grid_params.get("volumen_ratio", 0)
        if vol_ratio >= 3.0:
            score += 25
        elif vol_ratio >= 2.5:
            score += 20
        elif vol_ratio >= 2.0:
            score += 15
        
        # 3. Volatilidad óptima - peso 15%
        volatilidad = grid_params.get("volatilidad_pct", 0)
        if 2.0 <= volatilidad <= 5.0:  # Sweet spot
            score += 15
        elif 1.5 <= volatilidad <= 7.0:
            score += 10
        
        # 4. RSI en zona adecuada - peso 15%
        rsi = grid_params.get("rsi", 50)
        direccion = grid_params.get("direccion", "")
        if direccion == "LONG" and 55 <= rsi <= 65:
            score += 15
        elif direccion == "SHORT" and 35 <= rsi <= 45:
            score += 15
        elif direccion == "LONG" and 50 <= rsi <= 70:
            score += 10
        elif direccion == "SHORT" and 30 <= rsi <= 50:
            score += 10
        
        # 5. Historial de la moneda - peso 15%
        coin_score = self.get_coin_score(grid_params.get("symbol", ""))
        score += (coin_score / 100) * 15
        
        return min(100, score)
    
    def should_send_signal(self, grid_params):
        """Decide si enviar señal basado en calidad"""
        quality = self.calculate_signal_quality(grid_params)
        
        # Solo enviar señales de alta calidad (>60)
        if quality >= 70:
            return True, "EXCELENTE"
        elif quality >= 60:
            return True, "BUENA"
        else:
            return False, "BAJA CALIDAD"
