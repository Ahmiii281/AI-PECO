# Deployment Guide for AI-PECO

This guide covers deploying AI-PECO to production on Render (backend), Vercel (frontend), and MongoDB Atlas (database).

## Architecture Overview

```
┌─────────────────┐
│   Web Browser   │
└────────┬────────┘
         │
         └─→ Vercel (Frontend - React)
                    │
                    └─→ Render (Backend - FastAPI)
                               │
                               └─→ MongoDB Atlas (Database)

ESP32 Device ─→ Render Backend ─→ MongoDB Atlas
   (WiFi)
```

## Step 1: MongoDB Atlas (Database)

### Create Cluster

1. Go to https://www.mongodb.com/cloud/atlas
2. Sign up or log in
3. Click **Create** → **Build a Database**
4. Choose **Free Shared** tier
5. Select region **Asia (Singapore)** or closest to you
6. Click **Create**

### Create Database User

1. In cluster dashboard, click **Database Access** (left sidebar)
2. Click **Add New Database User**
3. Set username: `aipeco_user`
4. Set password: `ComplexPassword123!@#` (generate random)
5. Click **Add User**

### Whitelist IP

1. Click **Network Access** (left sidebar)
2. Click **Add IP Address**
3. Enter your IP or use `0.0.0.0/0` for development (insecure, not for production)
4. Click **Confirm**

### Get Connection String

1. Click **Connect** on your cluster
2. Choose **Drivers**
3. Select **Python 3.6 or later**
4. Copy the connection string:
   ```
   mongodb+srv://aipeco_user:PASSWORD@cluster0.xxxxx.mongodb.net/aipaco?retryWrites=true&w=majority
   ```
5. Replace `PASSWORD` with your database user password
6. Save this for backend `.env`

---

## Step 2: Backend Deployment (Render)

### Prepare Repository

Ensure your GitHub repo has this structure:
```
repository/
├── backend/
│   ├── ai/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── schemas/
│   ├── utils/
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/  (if in same repo)
└── README.md
```

### Deploy on Render

1. Go to https://render.com
2. Sign up with GitHub
3. Click **New** → **Web Service**
4. Connect your GitHub repository
5. Configure:
   - **Name:** `aipeco-backend`
   - **Region:** Singapore (or closest)
   - **Branch:** main
   - **Runtime:** Python 3.9
   - **Build Command:**
     ```bash
     pip install -r backend/requirements.txt
     ```
   - **Start Command:**
     ```bash
     uvicorn backend.main:app --host 0.0.0.0 --port $PORT
     ```
   
6. **Environment Variables** (click **Add Environment Variable** for each):
   ```ini
   MONGODB_URL = mongodb+srv://aipeco_user:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   DATABASE_NAME = aipeco_db
   SECRET_KEY = (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
   ACCESS_TOKEN_EXPIRE_MINUTES = 1440
   APP_NAME = AI-PECO Backend
   ```

7. **Plan:** Choose **Free** tier (free for now)
8. Click **Create Web Service**

⏳ **Deployment** will take 3-5 minutes. You'll see a URL like:
```
https://aipeco-backend-xxxxx.onrender.com
```

### Test Backend

```bash
curl https://aipeco-backend-xxxxx.onrender.com/health
# Should return: {"status": "ok"}
```

---

## Step 3: Frontend Deployment (Vercel)

### Prepare Repository

Push your code to GitHub. Ensure `package.json` is in root:
```json
{
  "name": "aipeco-frontend",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

### Deploy on Vercel

1. Go to https://vercel.com
2. Sign up with GitHub
3. Click **Add New** → **Project**
4. Select your repository
5. **Framework Preset:** Vite
6. **Root Directory:** `.` (or select the root folder)
7. **Build Command:** `npm run build`
8. **Output Directory:** `dist`
9. **Environment Variables:**
   ```
   VITE_API_URL = https://aipeco-backend-xxxxx.onrender.com
   ```
10. Click **Deploy**

⏳ **Deployment** will take 1-2 minutes. You'll see a URL like:
```
https://aipeco-frontend-xxxxx.vercel.app
```

### Test Frontend

1. Visit `https://aipeco-frontend-xxxxx.vercel.app`
2. Register a new account
3. Log in
4. Create a device

---

## Step 4: Update ESP32 Firmware

Edit `esp32/AIPECO.ino`:

```cpp
const char* backendUrl = "https://aipeco-backend-xxxxx.onrender.com";
```

Recompile and upload to ESP32.

---

## Step 5: Enable CORS in Production

Update `backend/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://aipeco-frontend-xxxxx.vercel.app",
        "http://localhost:3000",  # Local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Push to GitHub. Render will auto-redeploy.

---

## Optional: Custom Domain

### Domain via Vercel

1. In Vercel project settings
2. Go to **Domains**
3. Add your custom domain (e.g., `aipeco.com`)
4. Update DNS records at your registrar

### Domain via Render

1. In Render service settings
2. Go to **Custom Domain**
3. Add your domain
4. Update DNS records

---

## Monitoring & Logs

### Render Logs

1. Go to your Render service dashboard
2. Click **Logs** to see real-time output
3. Check for errors or warnings

### Vercel Logs

1. Go to your Vercel project
2. Click **Deployments**
3. Select latest deployment
4. View **Build Logs** and **Runtime Logs**

---

## Troubleshooting Deployment

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Ensure `requirements.txt` is in `backend/` folder |
| `Health check failed` | Check `main.py` has `/health` endpoint |
| Build fails | Check build command matches your folder structure |
| Frontend can't reach backend | Verify `VITE_API_URL` env var and CORS settings |
| Database connection error | Check MongoDB URI is correct, IP whitelisted |
| Token 401 error | Ensure `SECRET_KEY` is set in backend env vars |

---

## Production Checklist

- [ ] MongoDB Atlas cluster running
- [ ] Backend deployed on Render with all env vars set
- [ ] Frontend deployed on Vercel with VITE_API_URL set
- [ ] CORS properly configured for frontend domain
- [ ] ESP32 firmware updated with backend URL
- [ ] Database backups enabled (MongoDB Atlas)
- [ ] Monitoring alerts configured (optional)
- [ ] Domain names configured (optional)
- [ ] HTTPS enabled everywhere ✅ (automatic on Render/Vercel)

---

## Performance Tips

### Render
- Upgrade to **Standard** plan for auto-sleep prevention ($7/month)
- Monitor CPU/memory usage in metrics

### Vercel
- Use **Analytics** to track frontend performance
- Implement **Image Optimization** for large images

### MongoDB
- Create indexes on frequently queried fields:
  ```javascript
  db.devices.createIndex({ "user_id": 1 })
  db.energy_data.createIndex({ "device_id": 1, "timestamp": -1 })
  db.alerts.createIndex({ "user_id": 1, "resolved": 1 })
  ```

---

## Backup & Recovery

### MongoDB Backups

1. In MongoDB Atlas, go to **Backup** (left sidebar)
2. Enable **Automated Backups**
3. Set retention to 7+ days
4. Manual snapshots available

### Code Backups

GitHub stores your code. To roll back:
```bash
git log --oneline
git revert <commit-hash>
git push
# Render/Vercel will auto-redeploy
```

---

## Cost Breakdown (Monthly)

| Service | Free Tier | Cost |
|---------|-----------|------|
| **MongoDB Atlas** | 512 MB storage | Free forever |
| **Render** | Auto-sleeps | €5-50/month |
| **Vercel** | Unlimited builds | Free |
| **Domain** | N/A | ~$10/year |
| **Total** | Two services free | ~€5-50 + domain |

---

## Next Steps

1. ✅ Deploy backend & frontend
2. ✅ Test all API endpoints
3. ⏳ Monitor logs for 24 hours
4. ⏳ Set up email alerts (SendGrid, Mailgun)
5. ⏳ Configure CI/CD pipeline (GitHub Actions)
6. ⏳ Scale to production hardware

---

**Last Updated:** March 1, 2026  
**Status:** Ready for Production
