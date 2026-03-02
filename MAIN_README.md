# AI-PECO: AI-Powered Energy Consumption Optimizer

**Final Year Project** – A complete IoT + AI system for smart energy management using ESP32, FastAPI, React, and MongoDB.

## 📋 Project Overview

AI-PECO is a full-stack application that monitors energy consumption in real-time, provides AI-driven recommendations, and enables remote device control via relay automation. It supports:

- ✅ User authentication & role-based access (user/admin)
- ✅ Real-time energy monitoring with temperature & humidity sensors (DHT22)
- ✅ Simulated current readings (replace with SCT-013 later)
- ✅ Remote relay control via web dashboard
- ✅ AI recommendations based on consumption patterns
- ✅ Alert system for anomalies
- ✅ Beautiful, responsive React UI with dark mode

## 🗂 Folder Structure

```
AIPECO/
├── backend/                    # FastAPI backend
│   ├── ai/                    # AI/ML energy model
│   ├── routes/                # API endpoints
│   ├── services/              # Business logic
│   ├── models/                # Data models
│   ├── schemas/               # Request/response schemas
│   ├── utils/                 # JWT, hashing, security
│   ├── config.py              # Settings
│   ├── database.py            # MongoDB connection
│   ├── main.py                # FastAPI app
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Example environment variables
│   └── README.md              # Backend setup guide
├── esp32/                      # ESP32 firmware (Arduino)
│   └── AIPECO.ino            # DHT22 + relay + HTTP client
├── components/                 # React components
├── services/                   # Frontend API calls
├── hooks/                      # Custom React hooks
├── contexts/                   # React context (theme)
├── App.tsx                     # Main React component
├── index.tsx                   # React entry point
├── vite.config.ts             # Vite build config
├── tsconfig.json              # TypeScript config
├── package.json               # Frontend dependencies
├── .env.example                # Example frontend env vars
├── Dockerfile                 # Docker config for frontend
└── README.md                  # This file
```

## 🚀 Quick Start (Local Development)

### Prerequisites

- **Node.js 18+** – Frontend
- **Python 3.9+** – Backend
- **MongoDB Atlas** – Cloud database (free tier)
- **Arduino IDE** – ESP32 firmware upload

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate    # Windows
# or: source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your MongoDB URI and JWT secret

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`  
API docs: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
cd ..

# Install dependencies
npm install

# Create .env file
cp .env.example .env
# VITE_API_URL should be http://localhost:8000

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

### 3. ESP32 Firmware

1. **Install Arduino IDE** and set up ESP32 board support
2. **Open** `esp32/AIPECO.ino`
3. **Update** WiFi credentials and backend URL:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   const char* backendUrl = "http://YOUR_LOCAL_IP:8000";
   ```
4. **Upload** to ESP32 board

## 🔧 Configuration

### Backend (.env)

Create a `.env` file in the `backend/` directory:

```env
MONGODB_URL=mongodb+srv://user:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=aipeco_db
SECRET_KEY=your-super-secret-jwt-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440
APP_NAME=AI-PECO Backend
```

**Generate a secure SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Frontend (.env)

Create a `.env` file in the root directory:

```env
VITE_API_URL=http://localhost:8000
```

### ESP32 (AIPECO.ino)

Update these lines:
```cpp
const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";
const char* backendUrl = "http://192.168.x.x:8000";  // Your laptop's LAN IP

#define DHTPIN 32      // DHT22 data pin
#define RELAY1 26      // Relay 1 GPIO
#define RELAY2 27      // Relay 2 GPIO
#define RELAY3 25      // Relay 3 GPIO
#define RELAY4 33      // Relay 4 GPIO
```

## 📚 API Endpoints (Live Backend)

Most endpoints require a JWT token (login first and send `Authorization: Bearer <token>`),  
except the **ESP32 ingest endpoint** which is left open for development.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | User registration |
| POST | `/api/auth/login` | User login (returns JWT) |
| GET  | `/api/auth/me` | Get current user profile |
| GET  | `/api/devices` | List user's devices |
| POST | `/api/devices` | Create device |
| GET  | `/api/devices/{id}` | Get device details |
| PUT  | `/api/devices/{id}` | Update device |
| DELETE | `/api/devices/{id}` | Delete device |
| POST | `/api/energy/data` | Log sensor reading from ESP32 (public for dev) |
| GET  | `/api/energy/device/{id}` | Get device energy history (`hours` query param) |
| GET  | `/api/energy/alerts` | List user's alerts (`resolved` query param) |
| POST | `/api/energy/alerts` | Create alert |
| PUT  | `/api/energy/alerts/{id}` | Resolve alert |
| GET  | `/api/dashboard/stats` | Get dashboard stats (power, temp, humidity, alerts) |
| POST | `/api/dashboard/relay/{id}` | Send relay ON/OFF command |
| GET  | `/api/dashboard/device-command/{id}` | ESP32 polls latest relay command |
| GET  | `/api/dashboard/recommendation/{id}` | Get AI recommendation for a device |

See `backend/API_REFERENCE.md` for a complete, code-synced reference.  
Full interactive docs are also available at the backend `/docs` endpoint.

## 🏗 Deployment

### Backend (Render)

1. Push code to GitHub
2. Create Render account (free tier available)
3. Create new **Web Service**
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables:** Copy from `backend/.env.example`
4. Deploy

### Frontend (Vercel)

1. Push code to GitHub
2. Create Vercel account (free tier)
3. Import project
   - **Framework:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Environment Variable:** `VITE_API_URL` = your Render backend URL
4. Deploy

### Database (MongoDB Atlas)

1. Create free cluster at https://mongodb.com/cloud/atlas
2. Create database user
3. Whitelist IP in Network Access
4. Copy connection string to backend `.env`

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment guide.

## 🧪 Testing

### API Testing with cURL

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","password":"pass123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"pass123"}'

# Create device (use token from login response)
curl -X POST http://localhost:8000/api/devices \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"AC Unit","location":"Living Room","relay_pin":26}'

# Post sensor reading
curl -X POST http://localhost:8000/api/energy/data \
  -H "Content-Type: application/json" \
  -d '{
    "device_id":"GET_FROM_DEVICE_LIST",
    "current":2.5,
    "voltage":220,
    "power":550,
    "temperature":28.5,
    "humidity":65.2
  }'
```

## 🤖 AI & Energy Model

The AI module (`backend/ai/energy_model.py`) provides:

- **Linear Regression** – Predicts energy consumption based on temperature & current
- **Anomaly Detection** – Flags readings > mean + 2σ
- **Recommendations** – Suggests runtime reduction when temp exceeds threshold

Triggered when:
- User requests recommendation via dashboard
- Temperature anomaly detected
- Consumption exceeds historical average

## 🔄 Hardware Integration

### DHT22 Sensor
- **Pin:** GPIO 32
- **Data:** Temperature & humidity
- **Accuracy:** ±0.5°C, ±2% RH

### Relay Module (4-channel)
- **Relay 1:** GPIO 26
- **Relay 2:** GPIO 27
- **Relay 3:** GPIO 25
- **Relay 4:** GPIO 33
- **Control:** ON/OFF via web API or local temperature threshold

### Current Sensor
- **Current:** Simulated (0.5–5A) for development
- **Integration:** SCT-013 support planned (see below)

## 📈 Simulated vs Real Current

**Currently:** Current values are randomized for testing without hardware.

**To switch to SCT-013:**
```cpp
// In esp32/AIPECO.ino, replace:
simulatedCurrent = 0.5 + random(0, 4500) / 1000.0;

// With:
float readCurrent() {
  int raw = analogRead(SCT_PIN);
  float voltage = raw * (3.3 / 4096.0);
  return (voltage - 2.5) / 0.066;  // Calibration constant
}
...
simulatedCurrent = readCurrent();
```

Backend and AI module remain unchanged.

## 🧭 High-Level Architecture

```mermaid
flowchart LR
  userBrowser["User Browser"]
  reactApp["React Frontend (Vercel/Vite)"]
  fastapiApi["FastAPI Backend"]
  mongoDb["MongoDB Atlas"]
  esp32Board["ESP32 + DHT22 + Relays"]

  userBrowser --> reactApp
  reactApp -->|"HTTPS (REST, JWT)"| fastapiApi
  fastapiApi -->|"Sensor data, users, devices"| mongoDb
  esp32Board -->|"POST /api/energy/data"| fastapiApi
  fastapiApi -->|"GET /api/dashboard/device-command/{id}"| esp32Board
```

## 🔁 Data Flow: ESP32 → AI → Dashboard

```mermaid
flowchart LR
  esp32Node["ESP32 Firmware"]
  energyEndpoint["POST /api/energy/data"]
  energyServiceNode["EnergyService"]
  dbEnergy["MongoDB energy_data"]
  aiModelNode["EnergyModel"]
  dashboardEndpoint["GET /api/dashboard/recommendation/{device_id}"]
  reactDashboard["React DashboardView / ReportsView"]

  esp32Node -->|"JSON: current, voltage, power, temp, humidity"| energyEndpoint
  energyEndpoint --> energyServiceNode
  energyServiceNode --> dbEnergy
  energyServiceNode --> aiModelNode
  aiModelNode -->|"anomalies + savings estimate"| energyServiceNode
  reactDashboard --> dashboardEndpoint
  dashboardEndpoint --> aiModelNode
  dashboardEndpoint --> dbEnergy
  dashboardEndpoint --> reactDashboard
```

## 🎨 UI Features

- **Dark Mode Toggle** – `ThemeContext` + Tailwind
- **Real-Time Charts** – Recharts line graph
- **Alert Notifications** – Toast pop-ups
- **Responsive Design** – Mobile-friendly layout
- **Role-Based Menu** – Admin vs user views
- **Device Cards** – Status, temperature, power display

## 📝 Project Requirements Met

✅ User registration/login with JWT  
✅ Role-based access control (user/admin)  
✅ CRUD operations for devices  
✅ Real-time temperature & humidity monitoring  
✅ Relay control via API  
✅ Energy consumption tracking  
✅ AI-driven recommendations  
✅ Alert system  
✅ Admin panel  
✅ Production-ready code structure  
✅ Complete documentation  

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` in backend | Run from workspace root, check `.env` location |
| `401 Unauthorized` | Register first, ensure token is in header |
| MongoDB connection timeout | Check whitelist IP, verify credentials |
| Relay not responding | Check device exists, verify GPIO pin mapping |
| Frontend can't reach backend | Check `VITE_API_URL`, ensure backend is running |

See `backend/README.md` for more detailed troubleshooting.

## 📚 Documentation

- **Backend:** [backend/README.md](./backend/README.md)
- **Deployment:** [DEPLOYMENT.md](./DEPLOYMENT.md)
- **API Docs:** `http://localhost:8000/docs` (when running)

## 📦 Dependencies

### Backend
- FastAPI, Uvicorn
- Motor (async MongoDB)
- python-jose, passlib (authentication)
- scikit-learn, numpy (AI)
- pydantic

### Frontend
- React 18, Vite
- Tailwind CSS
- Recharts (visualization)
- Axios (HTTP)

### ESP32
- DHT.h, WiFi.h, HTTPClient.h, ArduinoJson.h

## 🎓 Final Year Project Info

| Aspect | Details |
|--------|---------|
| Project Name | AI-PECO (AI-Powered Energy Consumption Optimizer) |
| Technology Stack | FastAPI, React, ESP32, MongoDB |
| Duration | Full Semester |
| Team | Solo |
| Deliverables | Code, Documentation, Setup Guide |

## 📄 License

This project is open-source for educational purposes.

## 👤 Author

Developed as a Final Year Project  
**Date:** March 1, 2026

---

**Need Help?**  
Check [backend/README.md](./backend/README.md) or [DEPLOYMENT.md](./DEPLOYMENT.md)
