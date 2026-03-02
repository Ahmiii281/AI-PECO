# AI-PECO Backend Setup Guide

## Prerequisites

- Python 3.9+
- MongoDB Atlas Account (free tier available)
- pip or conda

## Local Setup (Development)

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Then open `.env` and update:

```env
# MongoDB Atlas connection string (from cluster overview)
MONGODB_URL=mongodb+srv://username:password@cluster0.xxxxxx.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=aipeco_db

# Generate a strong secret key for JWT
SECRET_KEY=your-super-secret-key-here-change-in-production

# Token expiry (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

**To generate a secure SECRET_KEY:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. MongoDB Atlas Setup

1. Create free account at https://www.mongodb.com/cloud/atlas
2. Create a new cluster (free tier)
3. Create a database user with username/password
4. Whitelist your IP (or use 0.0.0.0/0 for development)
5. Copy the connection string and paste into `.env` as `MONGODB_URL`

### 5. Run Backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

Test health endpoint:

```bash
curl http://localhost:8000/health
```

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive Swagger UI.

## Project Structure

```
backend/
├── ai/                    # AI/ML models for energy prediction
├── config.py              # Settings and environment variables
├── database.py            # MongoDB async connection
├── main.py                # FastAPI app entry point
├── models/                # Pydantic data models
├── routes/                # API route handlers
│   ├── auth.py           # Authentication endpoints
│   ├── devices.py        # Device CRUD
│   ├── energy.py         # Energy data logging
│   ├── dashboard.py      # Dashboard stats & relay control
│   ├── alerts.py         # Alert management
│   └── recommendations.py # Recommendations
├── schemas/               # Request/response schemas
├── services/              # Business logic services
└── utils/                 # Helper utilities (JWT, hashing)
```

## Database Schema

### users
- `_id`: ObjectId (auto)
- `name`: string
- `email`: string (unique)
- `password_hash`: string
- `role`: "user" | "admin"
- `energy_limit`: float

### devices
- `_id`: ObjectId
- `name`: string
- `location`: string
- `status`: "on" | "off"
- `relay_pin`: integer
- `user_id`: string (reference to users._id)

### energy_data
- `_id`: ObjectId
- `device_id`: string
- `current`: float (0.5–5A, can be simulated)
- `voltage`: float (220V)
- `power`: float (watts)
- `temperature`: float (°C from DHT22)
- `humidity`: float (% from DHT22)
- `timestamp`: datetime (UTC)

### alerts
- `_id`: ObjectId
- `user_id`: string
- `message`: string
- `resolved`: boolean
- `timestamp`: datetime

### recommendations
- `_id`: ObjectId
- `user_id`: string
- `message`: string
- `estimated_savings`: float
- `timestamp`: datetime

## Key Features

### Authentication & Authorization

- JWT-based token authentication
- Role-based access control (RBAC)
  - `user`: can manage own devices
  - `admin`: can manage all devices and users

### Endpoints

#### Auth
- `POST /api/auth/register` – User registration
- `POST /api/auth/login` – User login (returns JWT)
- `GET /api/auth/me` – Get current user profile

#### Devices
- `GET /api/devices` – List devices (filtered by user if not admin)
- `POST /api/devices` – Create new device
- `GET /api/devices/{device_id}` – Get device details
- `PUT /api/devices/{device_id}` – Update device
- `DELETE /api/devices/{device_id}` – Delete device

#### Energy Data
- `POST /api/energy/data` – Log sensor reading from ESP32 (public, no auth in dev)
- `GET /api/energy/device/{device_id}` – Get device history (`hours` query param)

#### Dashboard
- `GET /api/dashboard/stats` – Get stats (power, temp, etc.)
- `POST /api/dashboard/relay/{device_id}` – Send relay ON/OFF command
- `GET /api/dashboard/recommendation/{device_id}` – Get AI recommendation
- `GET /api/dashboard/device-command/{device_id}` – Poll for relay command (called by ESP32)

#### Alerts
- `GET /api/energy/alerts` – List alerts for current user (`resolved` query param)
- `POST /api/energy/alerts` – Create alert
- `PUT /api/energy/alerts/{alert_id}` – Resolve alert

## Deployment (Render)

### 1. Create Render Account

Visit https://render.com (free tier available)

### 2. Create Web Service

- Connect your GitHub repo
- **Build Command:** `pip install -r backend/requirements.txt`
- **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Add environment variables from `.env`

### 3. CORS Configuration

In production, update `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Troubleshooting

### `ModuleNotFoundError` during import

Ensure you're running from the workspace root and `.env` is in the `backend/` directory.

### Connection timeout to MongoDB

- Check internet connectivity
- Verify IP address is whitelisted in MongoDB Atlas
- Ensure `MONGODB_URL` and `DATABASE_NAME` are correct

### 401 Unauthorized

- Token may have expired (24-hour default)
- User may not have been created yet (register first)
- Frontend may not be sending `Authorization: Bearer {token}` header

### Relay command not working

- Ensure device exists and user has access
- Check `/api/dashboard/device-command/{device_id}` is being polled by ESP32
- Verify relay GPIO pins match firmware (`esp32/AIPECO.ino`)

## Testing Locally with cURL

```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"John","email":"john@example.com","password":"pass123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"pass123"}'

# Copy token from response, then:
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Create device
curl -X POST http://localhost:8000/api/devices \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"name":"AC Unit","location":"Living Room","relay_pin":26}'

# Post sensor reading (public in dev)
curl -X POST http://localhost:8000/api/energy/data \
  -H "Content-Type: application/json" \
  -d '{
    "device_id":"YOUR_DEVICE_ID",
    "current":2.5,
    "voltage":220,
    "power":550,
    "temperature":28.5,
    "humidity":65.2
  }'
```

## Next Steps

1. **Frontend**: Connect React app to this backend API
2. **ESP32**: Deploy firmware with correct `backendUrl`
3. **Monitoring**: Watch logs on Render dashboard
4. **Scaling**: Add email alerts, webhooks, or real SCT-013 integration

---

**Author:** AI-PECO Development Team  
**Last Updated:** March 1, 2026
