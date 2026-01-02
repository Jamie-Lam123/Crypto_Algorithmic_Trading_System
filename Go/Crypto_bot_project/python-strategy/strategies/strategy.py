import pandas as pd
import numpy as np

class StrategySMA_ATR:
    def __init__(self, fast_period=20, slow_period=50, atr_period=14, risk_per_trade=0.03):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.atr_period = atr_period
        self.risk_per_trade = risk_per_trade

    def prepare_indicators(self, df):
        """預先計算所有指標 (向量化計算，速度快)"""
        df = df.copy()
        # SMA
        df['SMA_Fast'] = df['Close'].rolling(window=self.fast_period).mean()
        df['SMA_Slow'] = df['Close'].rolling(window=self.slow_period).mean()
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(window=self.atr_period).mean()
        
        return df.dropna()

    def get_signal(self, curr_row, prev_row, balance, fee_rate):
        """
        輸入當前K線，返回交易指令
        Return: (Action, Size, StopLoss, TakeProfit, Reason)
        """
        price = curr_row['Close']
        atr = curr_row['ATR']

        # 買入信號 (金叉)
        if prev_row['SMA_Fast'] < prev_row['SMA_Slow'] and curr_row['SMA_Fast'] > curr_row['SMA_Slow']:
            
            # --- Risk Matrix 計算 ---
            sl_distance = 2.0 * atr
            calc_stop_loss = price - sl_distance
            calc_take_profit = price + (3.0 * atr)
            
            # 倉位計算
            risk_amount = balance * self.risk_per_trade
            theoretical_size = risk_amount / sl_distance if sl_distance > 0 else 0
            
            # 資金限制 (包含手續費緩衝)
            max_affordable = balance / (price * (1 + fee_rate))
            final_size = min(theoretical_size, max_affordable)
            
            return 'BUY', final_size, calc_stop_loss, calc_take_profit, "Golden Cross"

        # 賣出信號 (死叉)
        elif prev_row['SMA_Fast'] > prev_row['SMA_Slow'] and curr_row['SMA_Fast'] < curr_row['SMA_Slow']:
            return 'SELL', 0, 0, 0, "Death Cross"
            
        return 'HOLD', 0, 0, 0, None