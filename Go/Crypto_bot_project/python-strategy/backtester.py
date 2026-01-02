import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class BacktestEngine:
    def __init__(self, initial_balance=10000, fee_rate=0.001):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.fee_rate = fee_rate
        self.equity_curve = []
        self.signals = []
        self.trade_log = []

    def run(self, df, strategy_instance):
        """執行回測循環"""
        # 1. 計算指標
        df = strategy_instance.prepare_indicators(df)
        
        # 變數初始化
        in_position = False
        position_size = 0
        entry_price = 0
        stop_loss = 0
        take_profit = 0
        
        self.equity_curve = [] # 重置曲線
        
        print(f"--- Running Backtest on {len(df)} bars ---")

        for i in range(len(df)):
            curr_row = df.iloc[i]
            prev_row = df.iloc[i-1] if i > 0 else curr_row
            timestamp = df.index[i]
            price = curr_row['Close']
            
            # 更新權益曲線
            if in_position:
                mkt_value = position_size * price
                est_fee = mkt_value * self.fee_rate
                equity = self.balance + mkt_value - est_fee
            else:
                equity = self.balance
            self.equity_curve.append({'time': timestamp, 'equity': equity})

            if i < 1: continue

            # --- 檢查出場 (止盈/止損) ---
            if in_position:
                exit_reason = None
                if price <= stop_loss: exit_reason = "Stop Loss"
                elif price >= take_profit: exit_reason = "Take Profit"
                
                # 詢問策略是否要技術性賣出 (死叉)
                sig_type, _, _, _, sig_reason = strategy_instance.get_signal(curr_row, prev_row, self.balance, self.fee_rate)
                if sig_type == 'SELL': exit_reason = sig_reason

                if exit_reason:
                    # 執行賣出
                    revenue = position_size * price
                    fee = revenue * self.fee_rate
                    self.balance += (revenue - fee)
                    
                    pnl = (revenue - fee) - (entry_price * position_size * (1 + self.fee_rate))
                    
                    self.signals.append({'time': timestamp, 'price': price, 'type': 'SELL', 'reason': exit_reason})
                    self.trade_log.append({'pnl': pnl})
                    
                    in_position = False
                    position_size = 0

            # --- 檢查進場 ---
            elif not in_position:
                sig_type, size, sl, tp, reason = strategy_instance.get_signal(curr_row, prev_row, self.balance, self.fee_rate)
                
                if sig_type == 'BUY' and size > 0:
                    cost = size * price
                    fee = cost * self.fee_rate
                    if self.balance >= (cost + fee):
                        self.balance -= (cost + fee)
                        position_size = size
                        entry_price = price
                        stop_loss = sl
                        take_profit = tp
                        in_position = True
                        
                        self.signals.append({'time': timestamp, 'price': price, 'type': 'BUY', 'reason': reason})

        return pd.DataFrame(self.equity_curve).set_index('time')

    def print_performance(self):
        """打印績效報告"""
        if not self.trade_log:
            print("No trades generated.")
            return

        df_equity = pd.DataFrame(self.equity_curve)
        final_equity = df_equity['equity'].iloc[-1]
        total_return = (final_equity - self.initial_balance) / self.initial_balance * 100
        
        wins = [t['pnl'] for t in self.trade_log if t['pnl'] > 0]
        losses = [t['pnl'] for t in self.trade_log if t['pnl'] <= 0]
        win_rate = len(wins) / len(self.trade_log) * 100 if self.trade_log else 0
        
        print(f"\n{'='*30}")
        print(f"PERFORMANCE REPORT")
        print(f"{'='*30}")
        print(f"Final Equity : ${final_equity:.2f}")
        print(f"Total Return : {total_return:.2f}%")
        print(f"Total Trades : {len(self.trade_log)}")
        print(f"Win Rate     : {win_rate:.2f}%")
        print(f"Avg Win      : ${np.mean(wins) if wins else 0:.2f}")
        print(f"Avg Loss     : ${np.mean(losses) if losses else 0:.2f}")
        print(f"{'='*30}\n")

    def plot_results(self, df_price, title="Backtest Result"):
        """繪圖功能 (優化版：降頻以提升速度 + 死亡點標記)"""
        if not self.equity_curve:
            print("No data to plot.")
            return

        # 1. 轉換為 DataFrame
        df_equity = pd.DataFrame(self.equity_curve)
        if 'time' not in df_equity.columns: return
        df_equity['time'] = pd.to_datetime(df_equity['time'])
        df_equity.set_index('time', inplace=True)

        # 2. 數據降頻 (Resampling) - 關鍵！
        # 500萬點畫不出來，我們每 1 小時取一個點 (1H)
        # 這樣圖表會非常清晰，且秒開
        equity_resampled = df_equity['equity'].resample('4H').last().dropna()
        
        # 為了對照，價格也降頻
        price_resampled = df_price['Close'].resample('4H').last().dropna()
        
        # 找出對齊的時間段
        common_idx = equity_resampled.index.intersection(price_resampled.index)
        equity_resampled = equity_resampled.loc[common_idx]
        price_resampled = price_resampled.loc[common_idx]

        # 3. 找出「歸零」的時間點
        bust_date = None
        if equity_resampled.min() <= 0:
            # 找到第一個 <= 0 的時間
            bust_series = equity_resampled[equity_resampled <= 0]
            if not bust_series.empty:
                bust_date = bust_series.index[0]

        # --- 開始畫圖 ---
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [2, 1]})

        # 上圖：價格
        ax1.plot(price_resampled.index, price_resampled, label='BTC Price', color='gray', alpha=0.5)
        ax1.set_title(f'{title} - Market Trend')
        ax1.set_ylabel('Price')
        ax1.grid(True, alpha=0.3)
        
        # 如果有爆倉，畫一條紅線標記
        if bust_date:
            ax1.axvline(bust_date, color='red', linestyle='--', label=f'Busted at {bust_date.date()}')
            ax1.legend()

        # 下圖：資金曲線
        ax2.plot(equity_resampled.index, equity_resampled, color='blue', linewidth=1.5, label='Equity')
        
        # 畫初始本金線
        ax2.axhline(self.initial_balance, linestyle='--', color='orange', alpha=0.8, label='Initial Capital')
        
        # 填色：賺錢綠色，虧錢紅色
        ax2.fill_between(equity_resampled.index, self.initial_balance, equity_resampled, 
                         where=(equity_resampled >= self.initial_balance), facecolor='green', alpha=0.3)
        ax2.fill_between(equity_resampled.index, self.initial_balance, equity_resampled, 
                         where=(equity_resampled < self.initial_balance), facecolor='red', alpha=0.3)

        ax2.set_title(f'Equity Curve (Max Drawdown Analysis)')
        ax2.set_ylabel('Balance ($)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()