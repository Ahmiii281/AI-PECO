# AI-PECO - Energy Consumption Optimizer

AI-PECO is a full-stack IoT and AI-powered web application that helps users monitor, forecast, and optimize their electricity consumption. The system collects data from an ESP32 microcontroller, processes it using an AI-enhanced backend (Python/FastAPI), and visualizes it on a modern React dashboard.

---

## 🏗️ System Architecture

```text
+-------------------+        +----------------------+        +-------------------+
|     ESP32 IoT    |        |  AI-Backend (Python) |        | Frontend (React)  |
|                  |  HTTP  |                      |  HTTP  |                   |
| - DHT22 Sensor   |------->| - FastAPI Server     |<-------| - React 19        |
| - Relays (4x)    |        | - ML Predictions     |        | - Vite & Tailwind |
| - WiFi Client    |<-------| - JWT Auth & Control |        | - Recharts        |
+-------------------+        +----------+-----------+        +-------------------+
                                        |
                                        v
                               +----------------+
                               |    Database    |
                               | (MongoDB Atlas)|
                               +----------------+
```

### Folder Structure
- `/frontend` - React application (Vite, TypeScript, Tailwind)
- `/backend` - Python FastAPI application serving both general APIs and AI predictions
- `/esp32` - Arduino code for ESP32 microcontroller
- `/docs` - Additional setup documentation

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- Docker & Docker Compose (optional but recommended)
- MongoDB account (or local MongoDB container)

### 1. Installation

Clone the repository:
```bash
git clone https://github.com/Ahmiii281/AI-PECO.git
cd AI-PECO
```

### 2. Configuration Setup

Copy the example environment files and update them:

**Backend:**
```bash
cp backend/.env.example backend/.env
```
Update `backend/.env` with your `MONGODB_URL` and `SECRET_KEY`.

**Frontend:**
```bash
cp frontend/.env.example frontend/.env.local
```
*(By default, the frontend connects to `http://localhost:8000/api` which matches the local backend).*

**ESP32:**
Open `esp32/AIPECO.ino` and update the `backendUrl` variable to your PC's local IP address (e.g., `http://192.168.1.100:8000`).

---

## ⚙️ How to Run Locally

### Option A: Using Docker (Recommended)

Docker Compose will automatically build and start the Frontend, Backend, and a local MongoDB instance.

```bash
docker-compose up --build
```
- Frontend will be available at: `http://localhost:3000`
- Backend API & Docs at: `http://localhost:8000/docs`

### Option B: Using NPM Scripts

If you don't have Docker, you can run services directly on your host machine.

1. Install dependencies across all modules:
   ```bash
   npm run install:all
   ```

2. Start the development servers simultaneously:
   ```bash
   npm run dev
   ```
   *(Note: This requires Python to be accessible globally or from an activated virtual environment. Windows users may need to manually activate their venv in the backend folder first).*

---

## 🔗 API Endpoints Summary

Here are the primary endpoints exposed by the backend:

**Authentication**
- `POST /api/auth/register` - Create user account
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user profile

**IoT & Devices**
- `POST /api/energy/data` - Receive sensor data from ESP32
- `GET /api/dashboard/device-command/{device_id}` - ESP32 polls for relay commands
- `GET /api/devices` - List all registered devices
- `POST /api/dashboard/relay/{device_id}` - Turn device relay ON/OFF from frontend

**Analytics & AI**
- `GET /api/dashboard/stats` - Get aggregate system stats
- `GET /api/dashboard/recommendation/{device_id}` - Read AI energy optimization insights

*(For full interactive documentation, visit `http://localhost:8000/docs` while the backend is running).*

---

## 📄 License
This project is licensed under the MIT License.
