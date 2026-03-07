# Streamlit Cloud Deployment Guide

Deploy your Streamlit dashboard to Streamlit Cloud for **FREE** in 2 minutes.

## Prerequisites
- GitHub account with your repo pushed
- Streamlit account (free at https://share.streamlit.io)

## Step 1: Push Code to GitHub

```powershell
git add .
git commit -m "Ready for Streamlit Cloud deployment"
git push origin main
```

## Step 2: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Select:
   - **Repository:** Your GitHub repo
   - **Branch:** main
   - **File path:** app.py
4. Click **Deploy**

Your app will be live in 1-2 minutes with a URL like:
```
https://your-username-app-name.streamlit.app
```

## Step 3: Share & Monitor

- Get your live URL from the top of the page
- Check app status in the dashboard
- View logs if there are issues

## Advantages Over Railway

✅ **Free** - No credit card needed  
✅ **Unlimited** - No resource limits  
✅ **Automatic** - Updates when you push to GitHub  
✅ **Official** - Made by Streamlit team  
✅ **Simple** - No configuration needed  

## Troubleshooting

**App won't deploy?**
- Check that `app.py` is in repo root
- Verify all imports work locally first
- Check deployment logs in dashboard

**Missing dependencies?**
- Ensure `requirements.txt` is up to date:
  ```powershell
  pip freeze > requirements.txt
  git add requirements.txt
  git commit -m "Update dependencies"
  git push
  ```

**App crashes after deploy?**
- Check logs in Streamlit Cloud dashboard
- Usually missing dependencies or import errors
- Fix locally and push again

## That's It!

Your app is now live for free. Share the URL with anyone!
