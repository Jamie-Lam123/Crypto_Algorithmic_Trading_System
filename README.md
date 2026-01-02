# Crypto_Algorithmic_Trading_System
Crypto trading infrastructure with Go, Rust and Python

# Crypto Algorithmic Trading System (Hybrid Architecture)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Go](https://img.shields.io/badge/Go-1.21-00ADD8.svg)
![Python](https://img.shields.io/badge/Python-3.10-3776AB.svg)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)

An event-driven, hybrid algorithmic trading infrastructure designed for cryptocurrency markets. This project demonstrates a modular architecture separating **high-concurrency data ingestion** (Go) from **strategy research and backtesting** (Python).

---

## ⚠️ Note on Proprietary Strategies

**For Hiring Managers / Reviewers:**

This repository showcases the **system architecture**, **backtesting engine**, and **data pipeline**. 

Due to the proprietary nature of the alpha-generating logic used in live trading, the core strategy files have been redacted. A standard **SMA (Simple Moving Average) Crossover** strategy has been included in `python-strategy/strategies/ma_crossover.py` to demonstrate how the engine loads and executes trading logic.

---

## 🏗 System Architecture

The system follows a microservices-like architecture containerized via Docker:

### 1. Data Collector (Golang)
* **Role:** The "Eyes and Ears" of the system.
* **Tech:** Go (Goroutines, Channels).
* **Function:** Maintains persistent WebSocket connections with exchanges (e.g., Binance/OKX) to ingest real-time Tick/Orderbook data. It handles high-concurrency streams and normalizes data before passing it to the strategy engine.

### 2. Strategy Engine & Backtester (Python)
* **Role:** The "Brain" of the system.
* **Tech:** Python, Pandas, NumPy.
* **Function:** * **Live Mode:** Consumes normalized data, calculates technical indicators, and generates buy/sell signals.
    * **Backtest Mode:** A vectorized backtesting engine that simulates strategy performance against historical data (CSV), calculating metrics like Total Return, Drawdown, and Sharpe Ratio.

### 3. Infrastructure (Docker)
* The entire stack is orchestrated using `docker-compose`, ensuring consistent environments across development and deployment.

---

## 📂 Project Structure

```text
Crypto_Algorithmic_Trading_System/
├── go-collector/           # [Go] Real-time WebSocket data ingestion
│   ├── main.go             # Entry point for data collection
│   └── go.mod              # Go dependencies
│
├── python-strategy/        # [Python] Strategy logic & Backtesting
│   ├── main.py             # Orchestrator for running strategies
│   ├── backtester.py       # Event-driven/Vectorized backtest engine
│   ├── data_loader.py      # Data cleaning and ingestion
│   └── strategies/         # Strategy Logic Module
│       └── ma_crossover.py # (Sample Strategy for demonstration)
│
└── docker-compose.yml      # Container orchestration
