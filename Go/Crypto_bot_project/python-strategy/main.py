import matplotlib.pyplot as plt
from data_loader import DataLoader
from strategy import StrategySMA_ATR
from backtester import BacktestEngine

def main():
    # 1. 設置參數
    FILE_PATH = 'btcusd_1-min_data.csv' # 確保您的檔名正確
    INITIAL_CAPITAL = 10000
    FEE_RATE = 0.001 # 0.1%

    # 2. 載入並切分數據
    loader = DataLoader(FILE_PATH)
    test_set, validation_set = loader.split_data(split_ratio=0.8)

    # 3. 初始化策略
    # 您可以在這裡調整參數
    strategy = StrategySMA_ATR(fast_period=20, slow_period=50, atr_period=14)

    # 4. 初始化回測引擎
    engine = BacktestEngine(initial_balance=INITIAL_CAPITAL, fee_rate=FEE_RATE)

    # ==========================================
    # Phase 1: Test Set (Expanding Walk-Forward)
    # ==========================================
    print("\n>>> STARTING TEST SET (WALK FORWARD SIMULATION) <<<")
    
    # 這裡我們簡單模擬：直接跑完整個 Test Set
    # 如果要做 Rolling Window，可以寫一個迴圈切片 test_set
    engine.run(test_set, strategy)
    engine.print_performance()
    # ... (Phase 1 跑完後) ...
    
    engine.plot_results(test_set, title="Phase 1: Test Set Result")

    # 獲取 Test Set 結束後的餘額
    new_capital = engine.balance 
    print(f"Phase 1 結束餘額: ${new_capital:.2f}")

    # === 保護機制：如果已經破產，就不要跑 Phase 2 了 ===
    if new_capital <= 100: # 剩不到 100塊 就算破產
        print("\n❌ Account Busted in Test Phase. Skipping Validation Phase.")
    else:
        print("\n>>> STARTING VALIDATION SET <<<")
        val_engine = BacktestEngine(initial_balance=new_capital, fee_rate=FEE_RATE)
        val_engine.run(validation_set, strategy)
        val_engine.plot_results(validation_set, title="Phase 2: Validation Set")

if __name__ == "__main__":
    main()