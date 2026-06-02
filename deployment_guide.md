# AI-PECO Deployment Guide

This document explains how to deploy the **AI-PECO** system (Frontend, Backend, and Database).

## 1. Prerequisites
- **GitHub Account:** Your repository must be pushed to GitHub.
- **MongoDB Atlas:** A running MongoDB Atlas cluster.
- **Vercel Account:** For Frontend deployment.
- **Railway/Render Account:** For Backend (FastAPI) deployment.

## 2. Frontend Deployment (Vercel)
1. Go to [vercel.com](https://vercel.com) and click **"Add New Project"**.
2. Import the `AI-PECO` repository.
3. Vercel will automatically detect the `vercel.json` file in the root.
4. **Environment Variables:**
   - `VITE_API_URL`: Set this to your **deployed backend URL** (e.g., `https://aipeco-backend.up.railway.app`).
   - `VITE_USE_DEMO_DATA`: Set to `false` for live data or `true` for demonstration.
5. Click **"Deploy"**.

## 3. Backend Deployment (Vercel Serverless)
The FastAPI backend is deployed as a Vercel serverless function using `backend/vercel.json`.
1. Connect your GitHub **Backend** repo to **Vercel**: [github.com/Ahmiii281/AI-PECO-Backend](https://github.com/Ahmiii281/AI-PECO-Backend)
2. Vercel auto-detects `backend/vercel.json` configuration.
3. **Environment Variables** (Set in Vercel Dashboard):
   - `MONGODB_URL`: Your Atlas connection string.
   - `SECRET_KEY`: A secure random string for JWT (48+ chars).
   - `DEBUG`: `false` (production)
   - `CORS_ORIGINS`: `https://ai-peco-frontend.vercel.app`

## 4. Database Setup (MongoDB Atlas)
1. Ensure your MongoDB Atlas user has read/write permissions.
2. In the "Network Access" tab, add `0.0.0.0/0` (or the specific IP addresses of your deployed frontend/backend) to allow connections.

---
**Need Help?** Contact the AI-PECO development team for assistance with API integration or IoT configuration.
