# Quick Start Guide

Complete setup in 5 minutes.

## Prerequisites

- Node.js 18+ (for frontend)
- Python 3.9+ (for backend)
- MongoDB Atlas account (free tier available)
- Arduino IDE (for ESP32)

## 1️⃣ Backend Setup (2 min)

```bash
cd backend

# Windows
copy .env.example .env
run_dev.bat

# macOS/Linux
cp .env.example .env
chmod +x run_dev.sh
./run_dev.sh
```

**Configure `.env` before running:**
```env
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=aipeco_db
SECRET_KEY=generate-random-string
```

Visit: http://localhost:8000/docs

## 2️⃣ Frontend Setup (1 min)

**Open a new terminal:**

```bash
# Ensure you're in the project root

npm install
npm run dev
```

Visit: http://localhost:5173

## 3️⃣ MongoDB Setup (2 min)

1. Go to https://mongodb.com/cloud/atlas
2. Create FREE cluster
3. Create user: `aipeco_user` / password
4. Get connection string and paste into backend `.env`
5. Whitelist your IP

## 4️⃣ ESP32 Setup (optional)

1. Open `esp32/AIPECO.ino` in Arduino IDE
2. Update WiFi credentials:
   ```cpp
   const char* ssid = "YOUR_WIFI";
   const char* password = "YOUR_PASS";
   const char* backendUrl = "http://192.168.1.x:8000";  // Your laptop IP
   ```
3. Upload to board

## 🧪 Test the System

### Backend
```bash
curl http://localhost:8000/health
```

### Register User
1. Go to http://localhost:5173
2. Click **Register**
3. Create an account

### Create Device
1. Log in to dashboard
2. Click **Devices**
3. Create new device with relay pin (26, 27, 25, or 33)
4. Copy device ID

### Post Sensor Data (test)
```bash
curl -X POST http://localhost:8000/api/energy/data \
  -H "Content-Type: application/json" \
  -d '{
    "device_id":"DEVICE_ID_HERE",
    "current":2.5,
    "voltage":220,
    "power":550,
    "temperature":28.5,
    "humidity":65.2
  }'
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI entry point |
| `backend/.env` | Configuration (create from .env.example) |
| `backend/requirements.txt` | Python dependencies |
| `esp32/AIPECO.ino` | ESP32 firmware |
| `App.tsx` | React root component |
| `package.json` | Frontend dependencies |

## 🔧 Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` | Run from `backend` directory with venv activated |
| `MongoDB connection error` | Check MONGODB_URL / DATABASE_NAME, whitelist your IP |
| `401 Unauthorized` | Register/login first, check token in localStorage |
| Frontend can't reach backend | Check `VITE_API_URL` env var, ensure backend is running |
| ESP32 won't connect | Update WiFi SSID/password, use correct backend URL |

## 📚 Full Documentation

- Backend details: [backend/README.md](./backend/README.md)
- Deployment: [DEPLOYMENT.md](./DEPLOYMENT.md)
- Full project: [MAIN_README.md](./MAIN_README.md)

## 🚀 Next Steps

1. ✅ Explore dashboard
2. ✅ Create multiple devices
3. ✅ Check AI recommendations
4. ✅ Deploy to Render/Vercel (see DEPLOYMENT.md)

---

**Project:** AI-PECO (AI-Powered Energy Consumption Optimizer)  
**Updated:** March 1, 2026
