# AI-PECO Setup Guide

Complete setup instructions for the **AI-Powered Energy Consumption Optimizer** project.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Backend Setup](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [ESP32 Hardware Setup](#esp32-hardware-setup)
6. [Configuration](#configuration)
7. [Running the Application](#running-the-application)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

For a **quick demo** without hardware:

```bash
# 1. Backend
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env
python main.py

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev

# 3. Access
# Frontend: http://localhost:5173
# Backend Docs: http://localhost:8000/docs
```

---

## Prerequisites

### System Requirements

- **Python 3.9+** (for backend & AI/ML)
- **Node.js 18+** (for frontend)
- **MongoDB** (or use mock for development)
- **Git** (for version control)

### Installation

**Windows:**
```powershell
# Install Python from https://www.python.org/downloads/
# Install Node.js from https://nodejs.org/

# Verify installation
python --version
node --version
npm --version
```

**Linux/macOS:**
```bash
# Using homebrew (macOS)
brew install python node

# Using apt (Linux)
sudo apt install python3 nodejs npm
```

---

## Backend Setup

### 1. Create Virtual Environment

```bash
cd backend

# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**If pip install fails**, update pip:
```bash
pip install --upgrade pip
```

### 3. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env with your values
# At minimum, set:
# - DEBUG=True  (for development)
# - MONGODB_URL (or leave default for mock)
# - SECRET_KEY (auto-generated if empty in DEBUG mode)
```

### 4. Run Backend

```bash
python main.py
```

**Expected output:**
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Access:**
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
# Copy template
cp .env.example .env.local

# Edit if backend is on different URL (default: http://localhost:8000)
```

### 3. Run Development Server

```bash
npm run dev
```

**Expected output:**
```
VITE v... ready in ... ms

➜  Local:   http://localhost:5173/
```

**Access Dashboard:** http://localhost:5173

### 4. Build for Production

```bash
npm run build
npm run preview
```

---

## ESP32 Hardware Setup

### 1. Create Credentials File

```bash
cd esp32

# Copy template
cp credentials.h.example credentials.h

# Edit credentials.h with:
# - WIFI_SSID: Your WiFi network name
# - WIFI_PASSWORD: Your WiFi password
# - BACKEND_URL: Your PC's IP and port (e.g., http://192.168.1.100:8000)
# - DEVICE_API_KEY: Must match DEVICE_API_KEY in backend/.env
```

### 2. Find Your PC's IP Address

**Windows:**
```powershell
ipconfig
# Look for "IPv4 Address" under your network adapter (e.g., 192.168.1.100)
```

**Linux/macOS:**
```bash
ifconfig
# Look for "inet" address on your network interface
```

### 3. Upload to ESP32

1. Install **Arduino IDE** from https://www.arduino.cc/en/software
2. Install **ESP32 Board Support**:
   - File → Preferences
   - Add URL: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - OK → Tools → Board Manager → Search "esp32" → Install
3. Connect ESP32 via USB
4. Open `esp32/AIPECO.ino` in Arduino IDE
5. Tools → Board → Select "ESP32 Dev Module"
6. Tools → Port → Select your ESP32's COM port
7. Click Upload (→ button)

### 4. Monitor Serial Output

```bash
# After uploading, open Serial Monitor
# Tools → Serial Monitor (Ctrl+Shift+M)
# Speed: 115200 baud
```

**Expected logs:**
```
Connecting to WiFi...
WiFi connected! IP: 192.168.1.XXX
Backend: http://192.168.1.100:8000
Starting sensor readings...
```

---

## Configuration

### Backend Configuration (.env)

```env
# Application
DEBUG=True                 # False for production
APP_NAME=AI-PECO
APP_VERSION=1.0.0

# Security (CRITICAL for production)
SECRET_KEY=               # Auto-generated in DEBUG mode; required for production
DEVICE_API_KEY=esp32_key

# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=aipeco_db

# CORS (frontend URLs)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Demo Mode (when hardware not available)
DEMO_MODE=True
DEMO_ADMIN_PASSWORD=admin123

# Features
ENABLE_AI_PREDICTIONS=True
ENABLE_AUTO_ALERTS=True
```

### Frontend Configuration (.env.local)

```env
VITE_API_URL=http://localhost:8000
VITE_ENABLE_DEMO_MODE=true
```

### ESP32 Configuration (credentials.h)

```cpp
#define WIFI_SSID "Your_WiFi_Name"
#define WIFI_PASSWORD "Your_WiFi_Password"
#define BACKEND_URL "http://192.168.1.100:8000"
#define DEVICE_API_KEY "esp32_secure_api_key_here"
```

---

## Running the Application

### Development (All Components)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - ESP32 (optional):**
- Upload to ESP32 via Arduino IDE
- Monitor Serial Output for logs

### Production

```bash
# Backend
cd backend
pip install -r requirements.txt
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app

# Frontend
cd frontend
npm run build
# Deploy dist/ folder to hosting service
```

---

## Testing

### Backend API Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm run test
```

### Manual Testing

1. **Login**: http://localhost:5173 → Sign up/Login
2. **Dashboard**: View energy statistics
3. **Devices**: Add/manage IoT devices
4. **Predictions**: View AI energy forecasts
5. **Alerts**: Check anomaly alerts

---

## Troubleshooting

### Backend Won't Start

**Error: "SECRET_KEY must be set"**
```bash
# Solution: Set SECRET_KEY in .env
echo 'SECRET_KEY='$(python -c 'import secrets; print(secrets.token_urlsafe(32))') >> backend/.env
```

**Error: "MongoDB connection failed"**
```bash
# Solution 1: Install MongoDB locally
# https://www.mongodb.com/try/download/community

# Solution 2: Use mock database (default in DEBUG mode)
# Just set DEBUG=True in .env
```

### Frontend Can't Connect to Backend

**Error: "Failed to fetch from http://localhost:8000"**
```bash
# Solution: Ensure backend is running
# Check: http://localhost:8000/health
# If CORS error, check CORS_ORIGINS in backend/.env includes frontend URL
```

### ESP32 Won't Connect

**Error: "WiFi connection failed"**
1. Check WiFi SSID and password in credentials.h
2. Restart ESP32 (press RST button)
3. Check Serial Monitor for error messages

**Error: "Cannot reach backend"**
1. Verify backend IP address with `ipconfig` / `ifconfig`
2. Ensure ESP32 and backend are on same network
3. Check firewall allows port 8000
4. Verify `BACKEND_URL` in credentials.h

### Database Issues

**Error: "Energy data not saving"**
1. Check database connection: http://localhost:8000/health
2. Verify device exists in MongoDB
3. Check backend logs for errors

**Error: "Demo mode not generating data"**
1. Ensure `DEMO_MODE=True` in backend/.env
2. Restart backend
3. Check logs: `tail -f backend/logs/fastapi_errors.log`

---

## Project Structure

```
AI-PECO/
├── backend/
│   ├── api/                 # API endpoints
│   ├── services/            # Business logic
│   ├── models/              # Database models
│   ├── routes/              # Route definitions
│   ├── ai/                  # ML models & inference
│   ├── config.py            # Configuration
│   ├── main.py              # App entry point
│   ├── requirements.txt      # Python dependencies
│   └── .env.example         # Config template
│
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   └── App.tsx          # Root component
│   ├── package.json         # Node dependencies
│   └── .env.example         # Config template
│
├── esp32/
│   ├── AIPECO.ino           # Main ESP32 code
│   ├── credentials.h.example # Configuration template
│   └── lib/                 # Arduino libraries
│
└── docs/                    # Documentation
```

---

## Need Help?

1. **Backend Issues**: Check `backend/logs/fastapi_errors.log`
2. **Database Issues**: Verify MongoDB connection
3. **Frontend Issues**: Check browser console (F12)
4. **Hardware Issues**: Check ESP32 Serial Monitor (Baud: 115200)
5. **API Documentation**: http://localhost:8000/docs

---

## Next Steps

- [ ] Complete all setup steps above
- [ ] Verify all components are running
- [ ] Test dashboard functionality
- [ ] Add sample devices and data
- [ ] Review AI predictions
- [ ] Check ESP32 connectivity (if hardware available)

**Ready to evaluate? Ensure all components are running and dashboard is accessible.**

---

**Last Updated**: 2025-01-20
**Version**: 1.0.0
