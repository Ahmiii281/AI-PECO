# Configuration Reference

Complete guide to all AI-PECO configuration variables and what they do.

---

## Backend Configuration (backend/.env)

### Required Variables

#### `MONGODB_URL`
**Type:** String  
**Purpose:** MongoDB Atlas connection string  
**Format:** `mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority`

**Where to get:**
1. Go to MongoDB Atlas: https://mongodb.com/cloud/atlas
2. Create free cluster
3. Create database user (e.g. `aipeco_user`)
4. Click "Connect" → "Drivers" → "Python 3.6+"
5. Copy connection string and replace `PASSWORD`

**Example:**
```
MONGODB_URL=mongodb+srv://aipeco_user:MySecurePassword123@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=aipeco_db
```

#### `SECRET_KEY`
**Type:** String (random, secret)  
**Purpose:** JWT token signing secret  
**Security:** Change this in production!

**Generate secure key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Example:**
```
SECRET_KEY=gFz8K-jL9mN_pQ2rS3tU4vW5xY6zA7bC8dE9f
```

### Optional Variables

#### `ACCESS_TOKEN_EXPIRE_MINUTES`
**Type:** Integer  
**Default:** `1440` (24 hours)  
**Purpose:** JWT token expiration time  
**Range:** 10-20160 (recommended)

#### `APP_NAME`
**Type:** String  
**Default:** `"AI-PECO Backend"`  
**Purpose:** Application name (used in docs)

### Complete .env Example

```ini
MONGODB_URL=mongodb+srv://aipeco_user:MySecurePassword123@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=aipeco_db
SECRET_KEY=gFz8K-jL9mN_pQ2rS3tU4vW5xY6zA7bC8dE9f
ACCESS_TOKEN_EXPIRE_MINUTES=1440
APP_NAME=AI-PECO Backend
```

---

## Frontend Configuration (root/.env)

### Required Variables

#### `VITE_API_URL`
**Type:** URL string  
**Purpose:** Backend API base URL  

**Development:**
```ini
VITE_API_URL=http://localhost:8000
VITE_USE_DEMO_DATA=true
```

**Production (Render):**
```ini
VITE_API_URL=https://aipeco-backend-xxxxx.onrender.com
VITE_USE_DEMO_DATA=false
```

### Complete .env Example

```ini
VITE_API_URL=http://localhost:8000
VITE_USE_DEMO_DATA=true
```

---

## ESP32 Firmware Configuration (esp32/AIPECO.ino)

### WiFi Configuration

```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
```

**Where to find WiFi network name:**
- Look at available WiFi networks on your computer
- It's the name that appears in WiFi settings

### API Configuration

```cpp
const char* backendUrl = "http://192.168.1.100:8000";
```

**For Local Development:**
- Find your laptop's local IP: `ipconfig` (Windows) or `ifconfig` (macOS/Linux)
- Use IP from your network (typically 192.168.1.x or 10.0.0.x)

**For Production (Render):**
```cpp
const char* backendUrl = "https://aipeco-backend-xxxxx.onrender.com";
```

### Hardware Pin Configuration

```cpp
#define DHTPIN 32      // DHT22 data pin
#define RELAY1 26      // Relay 1 GPIO pin
#define RELAY2 27      // Relay 2 GPIO pin
#define RELAY3 25      // Relay 3 GPIO pin
#define RELAY4 33      // Relay 4 GPIO pin
```

**Important:** Don't change these unless you use different GPIO pins on your ESP32!

---

## Database Configuration (MongoDB Atlas)

### Cluster Settings

| Setting | Recommended Value |
|---------|------------------|
| **Tier** | Free (M0) |
| **Region** | Closest to you (SGP for Asia) |
| **Provider** | AWS/GCP/Azure (any) |
| **Backup** | Enabled (automatic) |

### Network Access

- **For Development:** Whitelist `0.0.0.0/0` (any IP)
- **For Production:** Whitelist specific IPs only

### User Permissions

```
Username: aipeco_user
Password: (secure random, 16+ chars)
Database: aipaco
Roles: Read and write to any database
```

### Collection Indexes (Optional, for Performance)

Create these indexes in MongoDB Atlas for faster queries:

```javascript
// In MongoDB Atlas Shell

use aipaco

// User indexes
db.users.createIndex({ "email": 1 }, { unique: true })

// Device indexes
db.devices.createIndex({ "user_id": 1 })
db.devices.createIndex({ "device_id": 1 })

// Energy data indexes
db.energy_data.createIndex({ "device_id": 1, "timestamp": -1 })
db.energy_data.createIndex({ "timestamp": 1 })

// Alert indexes
db.alerts.createIndex({ "user_id": 1, "resolved": 1 })

// Recommendation indexes
db.recommendations.createIndex({ "user_id": 1 })
```

---

## Deployment Environment Variables

### Render (Backend)

Set these in Render dashboard under "Environment":

```ini
MONGODB_URL=mongodb+srv://aipeco_user:password@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=aipeco_db
SECRET_KEY=your-secure-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440
APP_NAME=AI-PECO Backend
```

### Vercel (Frontend)

Set these in Vercel dashboard under "Settings" → "Environment Variables":

```
VITE_API_URL=https://aipeco-backend-xxxxx.onrender.com
```

---

## Advanced Configuration Options

### Backend API Rate Limiting (Optional)

To add rate limiting in `backend/main.py`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    ...
```

Install: `pip install slowapi`

### CORS Configuration (Production)

Update in `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://aipeco-frontend-xxxxx.vercel.app",
        "https://yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=600,  # Cache preflight for 10 minutes
)
```

### Database Query Optimization

For large datasets, add pagination to energy readings:

```python
@router.get("/api/energy/device/{device_id}")
async def history(device_id: str, skip: int = 0, limit: int = 100):
    return await energy_service.get_device_history(device_id, skip=skip, limit=limit)
```

---

## Configuration Validation Checklist

### Before Running Locally

- [ ] Backend `.env` file created from `.env.example`
- [ ] `MONGODB_URL` and `DATABASE_NAME` are correct and MongoDB Atlas IP is whitelisted
- [ ] `SECRET_KEY` is a random string (not "secretkey")
- [ ] Frontend `.env` has `VITE_API_URL=http://localhost:8000`
- [ ] Python 3.9+ installed
- [ ] Node.js 18+ installed

### Before Deploying to Production

- [ ] New `SECRET_KEY` generated (never use development key)
- [ ] MongoDB user has separate credentials for production
- [ ] CORS whitelist updated to include frontend domain
- [ ] ESP32 firmware updated with production backend URL
- [ ] Database backups enabled
- [ ] HTTPS enabled (automatic on Render/Vercel)
- [ ] Monitoring/logging configured

---

## Troubleshooting Configuration Issues

### "MongoDB connection refused"
- Check `MONGODB_URL` is correct
- Verify IP is whitelisted on MongoDB Atlas
- Test connection: `python -c "from motor.motor_asyncio import AsyncIOMotorClient; print('OK')"`

### "JWT token invalid"
- Ensure `SECRET_KEY` is the same between dev and prod
- Check token expiration: `ACCESS_TOKEN_EXPIRE_MINUTES`
- Verify token includes `sub` (email) and `role` claims

### "Frontend can't reach backend"
- Check `VITE_API_URL` is correct in `.env`
- Ensure backend is running: `curl VITE_API_URL/health`
- Check browser console for CORS errors

### "ESP32 won't connect to WiFi"
- Verify SSID and password are correct (case-sensitive)
- Check WiFi is 2.4 GHz (ESP32 doesn't support 5 GHz)
- Try resetting board: press RST button

---

## Security Best Practices

| Setting | Development | Production |
|---------|-------------|-----------|
| **CORS** | `["*"]` | Specific domains only |
| **SECRET_KEY** | Any random string | Long (32+ chars) random |
| **MongoDB IP** | `0.0.0.0/0` | Specific IPs |
| **HTTPS** | N/A | Enabled (auto on Render) |
| **Database** | No backup | Automated backups |
| **Logging** | Console | File + cloud |

---

## Configuration Files Quick Reference

| File | Location | Purpose |
|------|----------|---------|
| Backend config | `backend/.env` | API keys, database, JWT secret |
| Frontend config | `.env` | Backend API URL |
| Firmware config | `esp32/AIPECO.ino` | WiFi, pins, backend URL |
| Backend app config | `backend/config.py` | Reads `.env` file |
| Vite config | `vite.config.ts` | Frontend build settings |
| FastAPI main | `backend/main.py` | CORS, middleware |

---

**Last Updated:** March 1, 2026
