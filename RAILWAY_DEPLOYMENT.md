# Railway Deployment Guide - Streamlit

This guide walks you through deploying your Streamlit forecasting dashboard to Railway in 5 minutes.

## Prerequisites
- GitHub account (with your repo pushed)
- Railway account (free at https://railway.app)

## Step 1: Push Code to GitHub

```powershell
git add .
git commit -m "Update to Streamlit with Railway deployment"
git push origin main
```

## Step 2: Connect to Railway

1. Go to [railway.app](https://railway.app)
2. Sign up or log in
3. Click **"New Project"** 
4. Select **"Deploy from GitHub"**
5. Authorize GitHub and select your repo
6. Railway auto-detects Streamlit and sets up deployment

## Step 3: Configure Environment Variables (if needed)

In Railway dashboard:
- Go to **Variables**
- Add any environment variables (optional for Streamlit)

## Step 4: Deploy

Railway automatically deploys when you push to main branch.

- Check deployment status in **Deployments** tab
- View logs in **Logs** tab
- Get your live URL in **Settings** → **Domains**

## Troubleshooting

**App crashes?**
- Check logs: Railway Dashboard → Logs
- Ensure `Procfile` contains Streamlit command ✓
- Verify `requirements.txt` includes all dependencies ✓

**Port issues?**
- Railway assigns $PORT automatically
- Streamlit config handles it ✓

**File uploads not working?**
- Railway uses ephemeral storage (resets on redeploy)
- Solution: Use AWS S3 or similar cloud storage for persistence

## Alternative: Deploy from CLI

```bash
npm i -g @railway/cli
railway login
railway link
railway up
```

That's it! Your Streamlit app is live.

