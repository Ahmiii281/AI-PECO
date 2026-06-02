# AI-PECO Deployment Guide

> Full step-by-step guide for deploying AI-PECO to **Vercel** (both frontend and backend).
>
> **GitHub Repos:**
> - **Monorepo:** [github.com/Ahmiii281/AI-PECO](https://github.com/Ahmiii281/AI-PECO)
> - **Frontend Only:** [github.com/Ahmiii281/AI-PECO-Frontend](https://github.com/Ahmiii281/AI-PECO-Frontend)
> - **Backend Only:** [github.com/Ahmiii281/AI-PECO-Backend](https://github.com/Ahmiii281/AI-PECO-Backend)

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

## 3. Vercel — Backend Deployment (Serverless)

### 3.1 Create Backend API Project on Vercel
1. Go to [vercel.com](https://vercel.com) → **Add New Project**
2. Import the **Backend** repo: [github.com/Ahmiii281/AI-PECO-Backend](https://github.com/Ahmiii281/AI-PECO-Backend)
3. Vercel will auto-detect settings from `backend/vercel.json`
4. Framework preset: **Other** (for FastAPI)

### 3.2 Configure Build & Deploy Settings
Vercel uses the `backend/vercel.json` configuration automatically:
- **Build Command:** Handled by `@vercel/python`
- **Output Directory:** Root (FastAPI serves directly)
- **Environment:** `serverless-functions` runtime

### 3.3 Set Environment Variables

In Vercel → Backend Project → **Settings** → **Environment Variables**, add:

| Variable | Value | Notes |
|----------|-------|-------|
| `MONGODB_URL` | `mongodb+srv://user:pass@cluster.mongodb.net/...` | From Atlas step above |
| `DATABASE_NAME` | `aipeco_db` | |
| `SECRET_KEY` | *(run command below)* | **Never reuse dev key** |
| `DEBUG` | `false` | |
| `DEMO_MODE` | `true` | Set `false` when hardware connected |
| `CORS_ORIGINS` | `https://ai-peco-frontend.vercel.app,http://localhost:3000,http://localhost:5173` | Your frontend domain |
| `DEVICE_API_KEY` | *(random string)* | For ESP32 authentication |
| `DEVICE_API_KEY_REQUIRED` | `true` | |
| `ELECTRICITY_TARIFF_PKR` | `50.0` | Adjust to your tariff |
| `FRONTEND_URL` | `https://ai-peco-frontend.vercel.app` | For password reset links |
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
After Vercel deploys, visit your backend health endpoint:
```
https://ai-peco-backend.vercel.app/health
```
Expected response:
```json
{"status": "healthy", "app": "AI-PECO", "version": "1.0.0", ...}
```

---

## 4. Vercel — Frontend Deployment

### 4.1 Create Vercel Project
1. Go to [vercel.com](https://vercel.com) → **Add New Project**
2. Import the **Frontend** repo: [github.com/Ahmiii281/AI-PECO-Frontend](https://github.com/Ahmiii281/AI-PECO-Frontend)
3. Vercel will auto-detect settings from `frontend/vercel.json`

### 4.2 Set Environment Variables

In Vercel → your project → **Settings** → **Environment Variables**:

| Variable | Value | Notes |
|----------|-------|-------|
| `VITE_API_URL` | `https://ai-peco-backend.vercel.app` | **Must** include `https://` |
| `VITE_USE_DEMO_DATA` | `false` | Disable demo data in production |
| `VITE_DEMO_LOGIN` | `false` | Disable demo login in production |

> ⚠️ **Important**: The `VITE_API_URL` must include `https://` — without it, all API calls will fail.

### 4.3 Deploy
Click **Deploy**. Vercel uses this build command from `vercel.json`:
```bash
npm ci --legacy-peer-deps && npm run build
```

### 4.4 Verify Deployment
Visit your Vercel URL:
```
https://ai-peco-frontend.vercel.app
```
Then:
1. Sign up with a new account → `POST /api/auth/register`
2. Log in → `POST /api/auth/login`
3. Dashboard should load data → `GET /api/dashboard/stats`

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

### Backend (Vercel Serverless)
```env
MONGODB_URL=mongodb+srv://ba341914_db_user:<password>@aipecocluster.83ttwti.mongodb.net/?appName=aipecocluster
DATABASE_NAME=ba341914_db_users
SECRET_KEY=<48+ char random string>
DEBUG=false
DEMO_MODE=true
CORS_ORIGINS=https://ai-peco-frontend.vercel.app,http://localhost:3000,http://localhost:5173
DEVICE_API_KEY=<random string for ESP32>
DEVICE_API_KEY_REQUIRED=true
ELECTRICITY_TARIFF_PKR=50.0
FRONTEND_URL=https://ai-peco-frontend.vercel.app
```

### Frontend (Vercel)
```env
VITE_API_URL=https://ai-peco-backend.vercel.app
VITE_USE_DEMO_DATA=false
VITE_DEMO_LOGIN=false
```

---

## 7. Sanity Check Flow

Run this sequence to confirm everything works end-to-end:

```bash
# 1. Health check
curl https://ai-peco-backend.vercel.app/health

# 2. Register a user
curl -X POST https://ai-peco-backend.vercel.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"Test1234!"}'

# 3. Login
curl -X POST https://ai-peco-backend.vercel.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}'

# 4. Use the token from step 3 to get profile
curl https://ai-peco-backend.vercel.app/api/auth/me \
  -H "Authorization: Bearer <token_from_step_3>"
```

---

## 8. Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Backend deployment fails | Python build issue | Check logs: Vercel Dashboard → Deployments → Backend |
| Frontend API calls fail in production | Missing `https://` in `VITE_API_URL` | Verify in Vercel Dashboard: `VITE_API_URL=https://ai-peco-backend.vercel.app` |
| CORS error in browser | `CORS_ORIGINS` missing frontend URL | Check backend env var includes `https://ai-peco-frontend.vercel.app` |
| 404 on auth endpoints | Wrong API base URL | Verify frontend is calling `/api/auth/...` not `/auth/...` |
| MongoDB connection failed | Wrong Atlas URL or IP not whitelisted | Check `MONGODB_URL`, whitelist `0.0.0.0/0` in Atlas |
| Password reset email not sent | SMTP not configured | Set `SMTP_HOST/USER/PASS` in backend env, or tokens appear in logs (dev mode) |
| Cold start timeout | Vercel serverless cold start | Frontend has exponential backoff + 30s timeout for auth |
| Token validation fails | Mismatched `SECRET_KEY` | Ensure both deployments use same `SECRET_KEY` value |
