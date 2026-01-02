import pandas as pd

class DataLoader:
    def __init__(self, filepath):
        self.filepath = filepath
        self.df = None

    def load_data(self):
        """讀取並清洗數據"""
        print(f"Loading data from {self.filepath}...")
        self.df = pd.read_csv(self.filepath)
        
        # 處理時間格式
        if 'Timestamp' in self.df.columns:
            self.df['datetime'] = pd.to_datetime(self.df['Timestamp'], unit='s')
        elif 'timestamp' in self.df.columns:
            self.df['datetime'] = pd.to_datetime(self.df['timestamp'], unit='s')
        
        self.df.set_index('datetime', inplace=True)
        
        # 清除空值
        self.df.dropna(inplace=True)
        
        # 去重
        self.df = self.df[~self.df.index.duplicated(keep='first')]
        print(f"Data loaded: {len(self.df)} rows.")
        return self.df

    def split_data(self, split_ratio=0.8):
        """
        將數據切分為 Test Set (用於優化/滾動測試) 和 Validation Set (未知未來)
        split_ratio: 0.8 代表前 80% 是測試集，後 20% 是驗證集
        """
        if self.df is None:
            self.load_data()
            
        split_index = int(len(self.df) * split_ratio)
        
        test_set = self.df.iloc[:split_index].copy()
        validation_set = self.df.iloc[split_index:].copy()
        
        print(f"Data Split -> Test Set: {len(test_set)} | Validation Set: {len(validation_set)}")
        return test_set, validation_set