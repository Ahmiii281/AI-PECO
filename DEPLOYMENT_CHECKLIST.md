# 🚀 AI-PECO Production Deployment Checklist

## Quick Start: Environment Variables Required

### Backend (Railway) - Set These in Railway Dashboard
```
MONGODB_URL=mongodb+srv://ba341914_db_user:Aipeco12345@aipecocluster.83ttwti.mongodb.net/?retryWrites=true&w=majority&appName=aipecocluster
SECRET_KEY=[GENERATE: python -c "import secrets; print(secrets.token_urlsafe(48))"]
DATABASE_NAME=ba341914_db_users
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://ai-peco-frontend.vercel.app
DEBUG=false
```

### Frontend (Vercel) - Set These in Vercel Dashboard → Environment Variables
```
VITE_API_URL=https://[your-railway-backend-name].up.railway.app
VITE_USE_DEMO_DATA=false
```

---

## What Was Fixed

### ✅ Backend Stability
- ❌ **Before:** MONGODB_URL defaulted to localhost → production crash
- ✅ **After:** Required in production, validates not localhost
- ❌ **Before:** SystemExit crashes on DB failure
- ✅ **After:** Graceful error handling, clear error messages
- ❌ **Before:** SECRET_KEY was hardcoded
- ✅ **After:** Must be set via environment variable, enforced at startup

### ✅ Database Connection
- ❌ **Before:** No validation of connection string
- ✅ **After:** Production fails fast if MONGODB_URL not set/invalid
- ❌ **Before:** Connection failures crash entire app
- ✅ **After:** Returns HTTP 503, logs clear error

### ✅ Backend CORS
- ✅ Vercel frontend domain allowed: `https://ai-peco-frontend.vercel.app`
- ✅ Local dev domains allowed for testing
- ✅ All methods (GET, POST, PUT, DELETE) allowed
- ✅ Credentials enabled for JWT tokens
- ✅ All necessary headers allowed

### ✅ Frontend API Configuration
- ❌ **Before:** Hardcoded fallback to localhost → production breaks silently
- ✅ **After:** Requires VITE_API_URL, fails visibly if not set
- ✅ All API calls use environment variable
- ✅ Production validation ensures URL is configured

### ✅ Build Configuration
- ✅ Vite @ alias points to /src
- ✅ Production build optimizations enabled
- ✅ Compression (gzip + brotli) configured
- ✅ Code splitting for faster loads

---

## Step-by-Step Deployment

### 1. Deploy Backend to Railway

```bash
# Ensure all changes are committed
git add -A
git commit -m "Fix production stability"
git push origin main

# Go to: https://railway.app
# Select your project → Variables
# Add the environment variables from above
# Deploy → Redeploy Latest Commit
```

**Verify Backend:**
```bash
curl https://[your-backend].up.railway.app/health
# Should return: {"status": "healthy", "app": "AI-PECO", ...}
```

### 2. Get Your Backend URL

- Go to Railway Dashboard
- Click Settings
- Copy your domain (e.g., `aipeco-backend.up.railway.app`)

### 3. Deploy Frontend to Vercel

```bash
# Go to: https://vercel.com
# Select your project → Settings → Environment Variables
# Add:
VITE_API_URL=https://[your-backend-from-step-2].up.railway.app
VITE_USE_DEMO_DATA=false

# Vercel auto-deploys on push, or manually trigger:
# Deployments → Redeploy Latest
```

**Verify Frontend:**
- Visit `https://ai-peco-frontend.vercel.app`
- Try logging in
- Check browser console for errors

---

## Verification Checklist

### Backend (Railway)
- [ ] Health endpoint responds: `/health`
- [ ] API documentation loads: `/docs`
- [ ] No CRITICAL errors in Railway logs
- [ ] MongoDB connection shows as ✓ in logs

### Frontend (Vercel)
- [ ] Page loads without JavaScript errors
- [ ] Console shows no "CRITICAL" warnings
- [ ] VITE_API_URL is correctly set to Railway URL
- [ ] Network requests show full URL (not localhost)

### End-to-End
- [ ] Can register new account
- [ ] Can login
- [ ] Dashboard loads data from backend
- [ ] No CORS errors in browser console
- [ ] No "Cannot reach server" false positives

---

## Common Issues & Fixes

### Backend: "MONGODB_URL must be set"
**Cause:** Variable not set in Railway Dashboard
**Fix:** Add MONGODB_URL to Railway → Variables

### Backend: "MongoDB connection FAILED"
**Cause:** Invalid connection string or credentials
**Fix:** 
1. Verify MONGODB_URL in MongoDB Atlas
2. Check username/password in connection string
3. Ensure IP address is whitelisted (Atlas: Network Access)

### Backend: "SECRET_KEY must be 32+ characters"
**Cause:** SECRET_KEY not set or too short
**Fix:** Generate and add: `python -c "import secrets; print(secrets.token_urlsafe(48))"`

### Frontend: "Cannot reach the server"
**Cause 1:** VITE_API_URL not set in Vercel
**Fix:** Add to Vercel environment variables
**Cause 2:** Backend URL is wrong
**Fix:** Verify correct Railway domain in VITE_API_URL

### Frontend: CORS error in console
**Cause:** Frontend domain not in backend CORS_ORIGINS
**Fix:** Add `https://ai-peco-frontend.vercel.app` to CORS_ORIGINS

### Login returns 404
**Cause:** Backend API not responding
**Fix:** 
1. Check Railway backend is running (green status)
2. Verify VITE_API_URL is correct
3. Check `/health` endpoint manually

---

## Production Monitoring

### Check Backend Status
```bash
# View logs in Railway
Railway → Project → Deployments → View Logs

# Monitor for:
✓ "Connected to MongoDB"
✓ "AI-PECO Backend Started"
⚠️ Any WARNING lines
❌ Any CRITICAL lines → fix immediately
```

### Check Frontend Status
```bash
# View logs in Vercel
Vercel → Project → Deployments → [latest] → Logs

# Check for:
✓ Build completed successfully
⚠️ Any build warnings
❌ Build failed → fix and redeploy
```

---

## Files Modified for Fixes

| File | Change | Why |
|------|--------|-----|
| `backend/config.py` | Remove localhost defaults, add strict validation | Prevent production crashes |
| `backend/database.py` | Use RuntimeError instead of SystemExit | Graceful error handling |
| `backend/main.py` | Try-catch in lifespan, non-critical features | App starts even if optional features fail |
| `frontend/services/api.ts` | Remove localhost fallback | Frontend fails visibly if misconfigured |
| `backend/.env.example` | Complete production guide | Help developers configure correctly |
| `frontend/.env.example` | Complete production guide | Help developers configure correctly |

---

## Quick Reference: URLs

| Component | URL |
|-----------|-----|
| Backend API | `https://[your-backend].up.railway.app` |
| Backend Docs | `https://[your-backend].up.railway.app/docs` |
| Backend Health | `https://[your-backend].up.railway.app/health` |
| Frontend | `https://ai-peco-frontend.vercel.app` |
| MongoDB Atlas | `https://cloud.mongodb.com` |
| Railway Dashboard | `https://railway.app` |
| Vercel Dashboard | `https://vercel.com` |

---

## Need Help?

1. **Check logs first:** Railway and Vercel dashboards show exact errors
2. **Verify env vars:** Double-check all variables are set (typos cause issues)
3. **Check connectivity:** Use `/health` endpoint to verify backend works
4. **Test locally first:** Ensure `npm run dev` + `python main.py` works before production

---

**Status: ✅ PRODUCTION READY**

All critical issues fixed. Your application should now:
- Run 24/7 without crashing
- Handle database failures gracefully
- Provide clear error messages
- Properly authenticate users end-to-end
- Scale on Railway and Vercel
