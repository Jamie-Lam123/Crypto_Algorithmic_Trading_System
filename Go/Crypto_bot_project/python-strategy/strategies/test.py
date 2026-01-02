import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. 核心邏輯類 (Strategy & Risk)
# ==========================================

class TradingSystem:
    def __init__(self, initial_balance=10000, risk_per_trade=0.03):
        self.initial_balance = initial_balance
        self.balance = initial_balance      # 現金餘額
        self.risk_per_trade = risk_per_trade # 風險係數 (3%)
        self.equity_curve = []              # 記錄總權益變化
        self.trade_log = []                 # 交易日誌

    def calculate_indicators(self, df):
        """計算技術指標"""
        df = df.copy()
        # 1. 策略指標: 雙均線
        df['SMA_Fast'] = df['Close'].rolling(window=20).mean()
        df['SMA_Slow'] = df['Close'].rolling(window=50).mean()
        
        # 2. 風控指標: ATR (衡量市場波動率)
        # 用於動態計算止損距離
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(window=14).mean()
        
        return df.dropna()

    def run_backtest(self, df):
        """執行回測"""
        df = self.calculate_indicators(df)
        
        in_position = False
        entry_price = 0
        stop_loss = 0
        take_profit = 0
        position_size = 0 # 持有的 BTC 數量 (可以是小數，例如 0.123)
        
        signals = [] # 用於畫圖標記

        print(f"=== 回測開始 (初始本金: {self.initial_balance} U) ===")

        for i in range(len(df)):
            # 獲取當前數據
            curr_row = df.iloc[i]
            prev_row = df.iloc[i-1] if i > 0 else curr_row
            price = curr_row['Close']
            atr = curr_row['ATR']
            timestamp = df.index[i]

            # --- 1. 計算當前總權益 (Real-time Equity) ---
            # 總權益 = 手上的現金 + (持有的比特幣 * 當前價格)
            if in_position:
                current_equity = self.balance + (position_size * price)
            else:
                current_equity = self.balance
            
            self.equity_curve.append(current_equity)

            if i < 1: continue 

            # --- 2. 賣出邏輯 (止盈/止損 或 死叉) ---
            if in_position:
                reason = None
                if price <= stop_loss:
                    reason = "Stop Loss (止損)"
                elif price >= take_profit:
                    reason = "Take Profit (止盈)"
                elif prev_row['SMA_Fast'] > prev_row['SMA_Slow'] and curr_row['SMA_Fast'] < curr_row['SMA_Slow']:
                    reason = "Death Cross (死叉)"

                if reason:
                    # 執行賣出
                    revenue = price * position_size
                    pnl = revenue - (entry_price * position_size)
                    self.balance += revenue # 賣掉變回現金
                    
                    self.trade_log.append({
                        'Type': 'SELL', 'Price': price, 'Time': timestamp, 
                        'Reason': reason, 'PnL': pnl, 'Balance': self.balance
                    })
                    signals.append((timestamp, price, 'SELL'))
                    
                    # 重置狀態
                    in_position = False
                    position_size = 0
                    
                    # 打印交易結果
                    icon = "✅" if pnl > 0 else "❌"
                    print(f"{icon} 賣出 ({reason}) | 獲利: {pnl:>8.2f} U | 權益: {self.balance:.2f}")

            # --- 3. 買入邏輯 (金叉) ---
            elif not in_position:
                # 金叉: 快線上穿慢線
                if prev_row['SMA_Fast'] < prev_row['SMA_Slow'] and curr_row['SMA_Fast'] > curr_row['SMA_Slow']:
                    
                    # === 關鍵修改：修正倉位計算 ===
                    
                    # 1. 計算止損距離 (根據 ATR)
                    sl_distance = 2.0 * atr  
                    calc_stop_loss = price - sl_distance
                    calc_take_profit = price + (3.0 * atr)

                    # 2. 計算理想倉位 (Risk Logic)
                    # 為了只虧總本金的 3%，我應該買多少？
                    risk_amount = self.balance * self.risk_per_trade
                    if sl_distance > 0:
                        theoretical_size = risk_amount / sl_distance
                    else:
                        theoretical_size = 0

                    # 3. 計算實際能買多少 (Wallet Logic)
                    # 如果理想倉位太貴，就買滿 (All in)
                    max_affordable_size = self.balance / price
                    
                    # 取兩者較小值：想買的 vs 買得起的
                    final_size = min(theoretical_size, max_affordable_size)

                    # 執行買入
                    cost = final_size * price
                    if cost > 0:
                        self.balance -= cost # 扣除現金
                        entry_price = price
                        stop_loss = calc_stop_loss
                        take_profit = calc_take_profit
                        position_size = final_size
                        in_position = True
                        
                        signals.append((timestamp, price, 'BUY'))
                        print(f"🟢 買入 | 價格: {price:.2f} | 數量: {position_size:.4f} BTC (花費: {cost:.2f})")

        return df, signals

# ==========================================
# 2. 執行與繪圖
# ==========================================

# 1. 讀取數據
filename = 'btcusd_1-min_data.csv' 
print("正在讀取數據...")
df = pd.read_csv(filename)

# 2. 處理時間格式
try:
    df['datetime'] = pd.to_datetime(df['Timestamp'], unit='s')
except KeyError:
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
df.set_index('datetime', inplace=True)

# 3. 截取最近數據 (例如最近 10000 分鐘，約 7 天)
backtest_df = df.tail(1000000)

# 4. 初始化系統並運行
# Risk 設為 3% (0.03)
system = TradingSystem(initial_balance=10000, risk_per_trade=0.03)
result_df, signals = system.run_backtest(backtest_df)

# 5. 繪製雙圖 (價格 + 資金曲線)
print("正在繪製圖表...")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True, gridspec_kw={'height_ratios': [2, 1]})

# --- 上圖：價格與指標 ---
ax1.plot(result_df.index, result_df['Close'], label='Price', color='gray', alpha=0.3)
ax1.plot(result_df.index, result_df['SMA_Fast'], label='SMA 20', color='orange', alpha=0.8)
ax1.plot(result_df.index, result_df['SMA_Slow'], label='SMA 50', color='blue', alpha=0.8)

# 標記箭頭
for timestamp, price, type_ in signals:
    if type_ == 'BUY':
        ax1.scatter(timestamp, price, marker='^', color='green', s=100, zorder=5)
    elif type_ == 'SELL':
        ax1.scatter(timestamp, price, marker='v', color='red', s=100, zorder=5)

ax1.set_title('Strategy: SMA Cross + ATR Risk Matrix')
ax1.set_ylabel('Price (USD)')
ax1.legend(loc='upper left')
ax1.grid(True)

# --- 下圖：資金曲線 (重點！) ---
equity_data = system.equity_curve
# 確保長度一致
equity_plot = equity_data[-len(result_df):] if len(equity_data) > len(result_df) else equity_data

ax2.plot(result_df.index[:len(equity_plot)], equity_plot, color='black', linewidth=1.5, label='Total Equity')
# 繪製盈虧背景色 (綠色=賺錢, 紅色=虧錢)
ax2.axhline(y=10000, color='blue', linestyle='--', alpha=0.5, label='Initial Capital')
ax2.fill_between(result_df.index[:len(equity_plot)], 10000, equity_plot, 
                 where=(np.array(equity_plot) >= 10000), facecolor='green', alpha=0.2)
ax2.fill_between(result_df.index[:len(equity_plot)], 10000, equity_plot, 
                 where=(np.array(equity_plot) < 10000), facecolor='red', alpha=0.2)

ax2.set_title(f'Capital Graph (Final Equity: {system.balance:.2f} USD)')
ax2.set_ylabel('Balance (USD)')
ax2.legend(loc='upper left')
ax2.grid(True)

plt.tight_layout()
plt.show()