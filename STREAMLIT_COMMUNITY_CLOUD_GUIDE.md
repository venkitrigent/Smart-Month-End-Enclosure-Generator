# Streamlit Community Cloud Deployment Guide

## FREE Hosting for Your Frontend! 🎉

This guide shows you how to deploy your Streamlit frontend to **Streamlit Community Cloud** for FREE.

---

## Prerequisites

1. ✅ Backend deployed to Cloud Run
2. ✅ Backend URL (e.g., `https://month-end-close-api-xxxxx.run.app`)
3. ✅ API Key for authentication
4. ✅ GitHub account
5. ✅ Code pushed to GitHub

---

## Step 1: Push Code to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Smart Month-End Close System"

# Create repo on GitHub.com first, then:
git remote add origin https://github.com/YOUR_USERNAME/smart-month-end-close.git
git branch -M main
git push -u origin main
```

**IMPORTANT**: Make sure your repository structure looks like this:

```
smart-month-end-close/
├── frontend/
│   ├── app.py              # Your Streamlit app
│   ├── requirements.txt    # Python dependencies
│   └── .streamlit/         # Optional: Streamlit config
│       └── config.toml
├── adk-orchestrator/       # Backend code
└── README.md
```

---

## Step 2: Sign Up for Streamlit Community Cloud

1. Go to https://streamlit.io/cloud
2. Click **"Sign up"**
3. Sign up with your **GitHub account**
4. Authorize Streamlit to access your GitHub repositories

---

## Step 3: Deploy Your App

### 3.1: Create New App

1. Click **"New app"** button
2. Fill in the deployment form:
   - **Repository**: `YOUR_USERNAME/smart-month-end-close`
   - **Branch**: `main`
   - **Main file path**: `frontend/app.py`

### 3.2: Configure Secrets

1. Click **"Advanced settings"**
2. In the **"Secrets"** section, add:

```toml
# Backend Configuration
BACKEND_URL = "https://month-end-close-api-xxxxx-uc.a.run.app"

# API Key for Authentication
API_KEY = "your-api-key-from-backend-deployment"

# Optional: Firebase Config (if using Firebase Auth)
FIREBASE_API_KEY = "your-firebase-api-key"
FIREBASE_AUTH_DOMAIN = "your-project.firebaseapp.com"
FIREBASE_PROJECT_ID = "your-project-id"
```

**Where to get these values:**
- `BACKEND_URL`: From your Cloud Run backend deployment
- `API_KEY`: From your backend `.env` file or deployment output

### 3.3: Deploy

1. Click **"Deploy!"**
2. Wait 2-3 minutes for deployment
3. Your app will be live at: `https://your-app-name.streamlit.app`

---

## Step 4: Test Your Deployment

1. Open your Streamlit app URL
2. Try signing in (development mode allows any email/password)
3. Upload a CSV file
4. Check if it connects to your backend
5. Test the chat feature

---

## Step 5: Update Secrets (If Needed)

If you need to update your backend URL or API key:

1. Go to your app dashboard on Streamlit Community Cloud
2. Click the **"⋮"** menu → **"Settings"**
3. Go to **"Secrets"** tab
4. Update the values
5. Click **"Save"**
6. App will automatically restart

---

## Troubleshooting

### Issue: "Connection refused" or "Cannot connect to backend"

**Solution**: Check your `BACKEND_URL` in secrets:
- Make sure it's the correct Cloud Run URL
- Make sure it includes `https://`
- Make sure there's no trailing slash

### Issue: "Authentication failed"

**Solution**: Check your `API_KEY` in secrets:
- Make sure it matches the API key in your backend
- No extra spaces or quotes

### Issue: "Module not found"

**Solution**: Check `frontend/requirements.txt`:
- Make sure all dependencies are listed
- Push changes to GitHub
- Streamlit will automatically redeploy

### Issue: App is slow or times out

**Solution**: 
- Check your Cloud Run backend logs
- Make sure backend has enough memory (2Gi recommended)
- Check if BigQuery/Firestore are configured correctly

---

## Updating Your App

Whenever you push changes to GitHub, Streamlit Community Cloud will automatically redeploy:

```bash
# Make changes to your code
git add .
git commit -m "Update feature X"
git push origin main

# Streamlit will auto-deploy in 1-2 minutes
```

---

## Alternative: Deploy Frontend to Cloud Run

If you prefer to host everything on Google Cloud:

```bash
# Set environment variables
export GCP_PROJECT_ID=your-project-id
export BACKEND_URL=https://your-backend-url.run.app
export API_KEY=your-api-key

# Deploy
./deploy/deploy-frontend-cloudrun.sh
```

**Pros of Cloud Run**:
- Full control
- Same infrastructure as backend
- Can use VPC networking

**Pros of Streamlit Community Cloud**:
- FREE
- Automatic deployments from GitHub
- No infrastructure management
- Built-in SSL

---

## Cost Comparison

### Streamlit Community Cloud
- **Cost**: FREE
- **Limits**: 
  - 1 GB RAM per app
  - Unlimited apps (public repos)
  - 3 private apps

### Cloud Run (Frontend)
- **Cost**: Pay per use
  - ~$0.10-0.50 per day for low traffic
  - ~$5-15 per month for moderate traffic
- **Limits**: Based on your GCP quota

**Recommendation**: Use Streamlit Community Cloud for the frontend (FREE) and Cloud Run for the backend.

---

## Security Best Practices

1. **Never commit secrets to GitHub**
   - Use `.gitignore` for `.env` files
   - Use Streamlit secrets for configuration

2. **Use HTTPS only**
   - Both Streamlit Community Cloud and Cloud Run provide SSL automatically

3. **Rotate API keys regularly**
   - Generate new keys every 90 days
   - Update in both backend and frontend secrets

4. **Restrict backend access**
   - Use API key authentication
   - Consider adding rate limiting
   - Monitor Cloud Run logs for suspicious activity

---

## Your Deployment Checklist

- [ ] Backend deployed to Cloud Run
- [ ] Backend URL obtained
- [ ] API key generated and saved
- [ ] Code pushed to GitHub
- [ ] Streamlit Community Cloud account created
- [ ] App deployed on Streamlit Community Cloud
- [ ] Secrets configured (BACKEND_URL, API_KEY)
- [ ] App tested and working
- [ ] URL shared with users

---

## 🎉 You're Done!

Your Smart Month-End Close system is now live:

- **Backend**: `https://month-end-close-api-xxxxx.run.app`
- **Frontend**: `https://your-app.streamlit.app`

Share the Streamlit URL with your users!

---

## Support

If you encounter issues:

1. Check Streamlit Community Cloud logs (in app dashboard)
2. Check Cloud Run backend logs: `gcloud run services logs read month-end-close-api`
3. Verify all secrets are configured correctly
4. Test backend directly: `curl https://your-backend-url.run.app/health`
