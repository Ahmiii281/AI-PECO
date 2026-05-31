# AI-PECO Deployment Guide

> Full step-by-step guide for deploying AI-PECO to GitHub → Railway (backend) → Vercel (frontend).

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | ≥ 3.11 |
| Node.js | ≥ 18 |
| npm | ≥ 9 |
| Git | Any recent version |
| MongoDB Atlas account | Free tier is sufficient |

---

## 1. MongoDB Atlas Setup

1. Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas) and create a free cluster.
2. Create a **Database User** with a strong password.
3. Under **Network Access**, add `0.0.0.0/0` (allow all IPs) — Railway IPs are dynamic.
4. Click **Connect** → **Drivers** → copy the connection string:
   ```
   mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. Replace `<user>` and `<password>` with your credentials. Save this string — you'll need it for Railway.

---

## 2. GitHub Push

```bash
# From the project root (f:\AI-PECO)
git add .
git commit -m "fix: production readiness — schema errors, config aliases, deps, env"
git push origin main
```

> **Before pushing**, verify these files are NOT tracked (should be in .gitignore):
> - `backend/.env`
> - `frontend/.env.local`
> - `frontend/.env.production`
> - `backend/venv/`
> - `node_modules/`

```bash
# Confirm sensitive files are ignored
git status --short | grep -E "\.env|venv|node_modules"
# Should show nothing (all ignored)
```

---

## 3. Railway — Backend Deployment

### 3.1 Create Railway Project
1. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. Select `AI-PECO`
3. Railway will auto-detect Python (Nixpacks) via `backend/railway.json`

### 3.2 Configure Root Directory
In Railway project settings → **Source** → set **Root Directory** to: `backend`

### 3.3 Set Environment Variables

In Railway → your service → **Variables**, add:

| Variable | Value | Notes |
|----------|-------|-------|
| `MONGODB_URL` | `mongodb+srv://user:pass@cluster.mongodb.net/...` | From Atlas step above |
| `DATABASE_NAME` | `aipeco_db` | |
| `SECRET_KEY` | *(run command below)* | **Never reuse dev key** |
| `DEBUG` | `false` | |
| `DEMO_MODE` | `true` | Set `false` when hardware connected |
| `CORS_ORIGINS` | `https://ai-peco.vercel.app,http://localhost:3000` | Update with your Vercel URL |
| `DEVICE_API_KEY` | *(random string)* | For ESP32 authentication |
| `DEVICE_API_KEY_REQUIRED` | `true` | |
| `ELECTRICITY_TARIFF_PKR` | `50.0` | Adjust to your tariff |
| `FRONTEND_URL` | `https://ai-peco.vercel.app` | For password reset links |
| `PORT` | `8080` | Railway sets this automatically |
| `SMTP_HOST` | *(optional)* | e.g., `smtp.gmail.com` |
| `SMTP_PORT` | `587` | |
| `SMTP_USER` | *(optional)* | Your email |
| `SMTP_PASS` | *(optional)* | App password |
| `SMTP_FROM` | `no-reply@ai-peco.com` | |

**Generate a strong SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 3.4 Verify Deployment
After Railway deploys, visit your Railway URL:
```
https://ai-peco-production.up.railway.app/health
```
Expected response:
```json
{"status": "healthy", "app": "AI-PECO", "version": "1.0.0", ...}
```

---

## 4. Vercel — Frontend Deployment

### 4.1 Create Vercel Project
1. Go to [vercel.com](https://vercel.com) → **Add New Project** → Import `AI-PECO`
2. Vercel will auto-detect settings from `vercel.json` (already configured)

### 4.2 Set Environment Variables

In Vercel → your project → **Settings** → **Environment Variables**:

| Variable | Value | Environment |
|----------|-------|-------------|
| `VITE_API_URL` | `https://ai-peco-production.up.railway.app` | Production |
| `VITE_USE_DEMO_DATA` | `false` | Production |
| `VITE_DEMO_LOGIN` | `false` | Production |
| `VITE_API_URL` | `http://localhost:8080` | Development |

> ⚠️ **Important**: The `VITE_API_URL` must include `https://` — without it, all API calls will fail.

### 4.3 Deploy
Click **Deploy**. Vercel uses this build command from `vercel.json`:
```bash
cd frontend && npm ci --legacy-peer-deps && npm run build
```

### 4.4 Verify Deployment
Visit your Vercel URL (e.g., `https://ai-peco.vercel.app`) and:
1. Sign up with a new account
2. Log in
3. Check the dashboard loads data

---

## 5. Local Development

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
# Copy and edit the .env file
cp .env.example .env
uvicorn main:app --reload --port 8080
```

API docs available at: `http://localhost:8080/docs`

### Frontend
```bash
cd frontend
npm install
# Ensure .env.local has VITE_API_URL=http://localhost:8080
npm run dev
```

App available at: `http://localhost:3000`

---

## 6. Required Environment Variables Summary

### Backend (Railway)
```env
MONGODB_URL=mongodb+srv://...
DATABASE_NAME=aipeco_db
SECRET_KEY=<48+ char random string>
DEBUG=false
DEMO_MODE=true
CORS_ORIGINS=https://ai-peco.vercel.app,http://localhost:3000
DEVICE_API_KEY=<random string for ESP32>
DEVICE_API_KEY_REQUIRED=true
ELECTRICITY_TARIFF_PKR=50.0
FRONTEND_URL=https://ai-peco.vercel.app
```

### Frontend (Vercel)
```env
VITE_API_URL=https://ai-peco-production.up.railway.app
VITE_USE_DEMO_DATA=false
VITE_DEMO_LOGIN=false
```

---

## 7. Sanity Check Flow

Run this sequence to confirm everything works end-to-end:

```bash
# 1. Health check
curl https://ai-peco-production.up.railway.app/health

# 2. Register a user
curl -X POST https://ai-peco-production.up.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"Test1234!"}'

# 3. Login
curl -X POST https://ai-peco-production.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}'

# 4. Use the token from step 3 to get profile
curl https://ai-peco-production.up.railway.app/api/auth/me \
  -H "Authorization: Bearer <token_from_step_3>"
```

---

## 8. Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Railway build fails | Wrong root directory | Set root dir to `backend` in Railway |
| `AttributeError: 'Settings' object has no attribute 'ENERGY_PRICE_PER_UNIT'` | Old code running | Deploy latest commit |
| `PydanticUndefinedAnnotation: UserResponse` | Old code running | Deploy latest commit |
| Frontend API calls fail in production | Missing `https://` in `VITE_API_URL` | Set env var in Vercel dashboard |
| MongoDB connection failed | Wrong Atlas URL or IP not whitelisted | Check URL, whitelist `0.0.0.0/0` in Atlas |
| CORS error in browser | `CORS_ORIGINS` missing Vercel URL | Add your Vercel URL to Railway `CORS_ORIGINS` env var |
| Password reset email not sent | SMTP not configured | Check `SMTP_HOST/USER/PASS` or tokens appear in Railway logs (dev mode only) |
| `bcrypt` version warning | Old requirements installed | Re-run `pip install -r requirements.txt` |
