# AI-PECO
AI-Powered Energy Consumption Optimizer

## Overview
AI-PECO uses machine learning (IsolationForest) and IoT integrations to optimize power usage, detect anomalies, and recommend energy savings.

## Production Setup with Docker

1. **Clone the repository:**
```bash
git clone https://github.com/Ahmiii281/AI-PECO.git
cd AI-PECO
```

2. **Environment Variables:**
Create your `.env` file from the example:
```bash
cp .env.example .env
```
Edit `.env` to supply production secrets (e.g., strong `SECRET_KEY`, actual `MONGODB_URL`).

3. **Start the Application:**
Use Docker Compose to build and start the backend + MongoDB:
```bash
docker-compose up -d --build
```

The FastAPI backend will run on `http://localhost:8000`.

## Architecture Highlights
- **FastAPI Backend:** Fully async operations with clean Dependency Injection for Db. Robust logging replaces generic prints.
- **Machine Learning:** `EnergyModel` pipeline detects anomalous measurements via Scikit-Learn `IsolationForest`.
- **Database Pooling:** `motor` async MongoDB interactions with resilient Connection Pools.

_For raw development natively, install dependencies via `pip install -r backend/requirements.txt`._
