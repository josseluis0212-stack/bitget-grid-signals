from strategy.scanner import TrendScanner
from core.exchange import BitgetConnector
import pandas as pd

class MockConnector:
    def __init__(self):
        self.exchange = type('obj', (object,), {'markets': {
            'BTC/USDT': {'precision': {'price': 1}},
            'XPIN/USDT': {'precision': {'price': 7}},
            'PEPE/USDT': {'precision': {'price': 10}}
        }})

def test_precision():
    connector = MockConnector()
    scanner = TrendScanner(connector)
    
    # Mock DF
    df = pd.DataFrame({
        'close': [0.0019266],
        'bb_lower': [0.0019100],
        'bb_middle': [0.0019250],
        'bb_upper': [0.0019400]
    })
    
    # Test XPIN
    params = scanner.calculate_grid_params('XPIN/USDT', df, 'LONG')
    print(f"XPIN LONG Params: {params}")
    assert params['min'] != params['max']
    
    # Test BTC
    df_btc = pd.DataFrame({
        'close': [65000.5],
        'bb_lower': [64000.0],
        'bb_middle': [65000.0],
        'bb_upper': [66000.0]
    })
    params_btc = scanner.calculate_grid_params('BTC/USDT', df_btc, 'LONG')
    print(f"BTC LONG Params: {params_btc}")

if __name__ == "__main__":
    test_precision()
