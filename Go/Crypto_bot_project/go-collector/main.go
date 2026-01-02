package main

import (
	"encoding/json"
	"log"
	"time"

	"github.com/gorilla/websocket"
)

// 1. 定義數據結構 (Struct)
// Python: 不需要定義，直接用 dict['c']。
// Go: 必須先定義結構。這裡我們只提取我們需要的字段。
type BinanceTicker struct {
	Symbol string `json:"s"` // "s" 是 Binance JSON 裡的 key，映射到 Go 的 Symbol 變量
	Price  string `json:"c"` // "c" 代表最新成交價 (Current Price)
}

// 定義 WebSocket 地址 (Binance 現貨市場 - Mini Ticker 1000ms 推送一次)
const wsURL = "wss://stream.binance.com:9443/ws/btcusdt@miniTicker"

func main() {
	// 2. 建立一個 Channel (通道)
	// Python: 類似 Queue.Queue()
	// 作用: 讓 "接收數據的協程" 和 "處理數據的協程" 解耦。
	priceChan := make(chan string)

	// 3. 啟動 "消費者" Goroutine (模擬寫入 Redis 的部分)
	// 關鍵點: 這個協程一旦啟動，就會一直運行，不會因為 WebSocket 斷線而停止。
	go func() {
		for price := range priceChan {
			// 在這裡，未來您會把代碼換成: redisClient.Set("BTC", price)
			log.Printf("收到價格並處理: %s", price)
		}
	}()

	// 4. 主循環: 負責 "生產數據" 和 "斷線重連"
	// 這是一個死循環，確保程序永遠不退出
	for {
		log.Println("正在連接 Binance WebSocket...")

		// 嘗試連接
		err := connectAndListen(priceChan)

		// 如果 connectAndListen 返回了，說明斷線了
		if err != nil {
			log.Printf("連接錯誤 (斷線): %v", err)
		}

		log.Println("5秒後嘗試重連...")
		time.Sleep(5 * time.Second) // 等待 5 秒再重連，避免請求過於頻繁被封 IP
	}
}

// 這是負責維持連接的函數
func connectAndListen(ch chan<- string) error {
	// Dial 建立連接
	c, _, err := websocket.DefaultDialer.Dial(wsURL, nil)
	if err != nil {
		return err
	}
	
	// defer 是 Go 的神技。
	// 意思: "無論這個函數是如何結束的 (報錯、return、崩潰)，最後一定要執行 c.Close()"
	// Python: 類似 try...finally { c.close() }
	defer c.Close()

	log.Println("連接成功！開始接收數據...")

	// 讀取循環
	for {
		_, message, err := c.ReadMessage()
		if err != nil {
			// 這裡捕捉到錯誤（比如拔掉網線），返回 err，觸發外層的重連邏輯
			return err
		}

		// 解析 JSON
		var ticker BinanceTicker
		// Unmarshal 就是 Python 的 json.loads()
		if err := json.Unmarshal(message, &ticker); err != nil {
			log.Printf("JSON 解析錯誤: %v", err)
			continue
		}

		// 將價格發送到 Channel
		// 注意: 這裡是非阻塞的，數據丟進去，上面的 "消費者 Goroutine" 就會收到
		ch <- ticker.Price
	}
}