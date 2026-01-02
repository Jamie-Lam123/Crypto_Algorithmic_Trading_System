# Crypto Algorithmic Trading System (Polyglot Architecture)

![Go](https://img.shields.io/badge/Go-Data_Ingestion-00ADD8.svg)
![Python](https://img.shields.io/badge/Python-Strategy_Research-3776AB.svg)
![Rust](https://img.shields.io/badge/Rust-Order_Execution-orange.svg)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)

An event-driven, hybrid algorithmic trading infrastructure designed for cryptocurrency markets. This project demonstrates a **Polyglot Architecture**, leveraging the strengths of three languages:
1.  **Go** for high-concurrency data ingestion.
2.  **Python** for statistical analysis and strategy logic.
3.  **Rust** for ultra-low latency order execution.

---

## ⚠️ Note on Proprietary Strategies
**For Hiring Managers:** This repository showcases the **system architecture** and **engineering stack**. Proprietary alpha strategies have been redacted. A standard SMA Crossover strategy is provided for demonstration.

---

## 🏗 System Architecture

The system is designed as a set of microservices:

### 1. Data Collector (Golang)
* **Role:** The "Eyes".
* **Function:** Maintains persistent WebSocket connections with exchanges (Binance/OKX). Handles high throughput (10k+ ticks/sec) and normalizes data.

### 2. Strategy Engine (Python)
* **Role:** The "Brain".
* **Function:** Consumes normalized data, calculates technical indicators (Pandas/NumPy), and runs vectorized backtests. It generates high-level `BUY/SELL` signals.

### 3. Execution Gateway (Rust) ⚡
* **Role:** The "Hands" (Critical Path).
* **Function:** * Listens for trade signals from the Python engine.
    * Performs **microsecond-level** risk checks.
    * Handles API signing and dispatches HTTP/WebSocket orders to the exchange with minimal latency.
    * Implemented in Rust for memory safety and zero-cost abstractions.

---

## 📂 Project Structure

```text
Crypto_Algorithmic_Trading_System/
├── go-collector/           # [Go] Real-time WebSocket data ingestion
├── python-strategy/        # [Python] Strategy logic & Backtesting
│   └── strategies/         # Strategy Logic Module
├── rust-executor/          # [Rust] Low-latency Order Execution Engine
│   └── src/main.rs         # Async execution loop
└── docker-compose.yml      # Container orchestration
