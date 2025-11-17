# Firebase Service Account Setup Guide

## What is Firebase Service Account?

Firebase Service Account is a JSON file that allows your backend to authenticate users and verify Firebase ID tokens. It's **optional** - you can use API key authentication instead.

---

## Option 1: Skip Firebase (Use API Key Only) - RECOMMENDED FOR QUICK START

If you want to deploy quickly without Firebase:

1. **In your `.env` file, comment out or remove:**
```bash
# FIREBASE_SERVICE_ACCOUNT=path/to/firebase-service-account.json
```

2. **Use API key authentication only:**
```bash
API_KEYS=your-generated-api-key
```

3. **Done!** Your app will work with API key authentication.

---

## Option 2: Set Up Firebase (For Production User Authentication)

### Step 1: Create Firebase Project

1. Go to https://console.firebase.google.com/
2. Click **"Add project"** or select existing project
3. Enter project name (can be same as your GCP project)
4. Click **"Continue"** → **"Continue"** → **"Create project"**

### Step 2: Enable Authentication

1. In Firebase Console, click **"Authentication"** in left menu
2. Click **"Get started"**
3. Click **"Email/Password"** under Sign-in providers
4. Toggle **"Enable"**
5. Click **"Save"**

### Step 3: Generate Service Account Key

1. In Firebase Console, click the **⚙️ gear icon** → **"Project settings"**
2. Go to **"Service accounts"** tab
3. Click **"Generate new private key"**
4. Click **"Generate key"** in the popup
5. A JSON file will download (e.g., `your-project-firebase-adminsdk-xxxxx.json`)

### Step 4: Save the Service Account File

**Option A: Local Development**
```bash
# Save to your project
mv ~/Downloads/your-project-firebase-adminsdk-xxxxx.json \
   adk-orchestrator/firebase-service-account.json

# Update .env
echo "FIREBASE_SERVICE_ACCOUNT=./firebase-service-account.json" >> adk-orchestrator/.env
```

**Option B: Cloud Run Deployment**

For Cloud Run, you have 2 options:

**Method 1: Use Secret Manager (Recommended)**
```bash
# Create secret
gcloud secrets create firebase-service-account \
  --data-file=firebase-service-account.json \
  --project=your-project-id

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding firebase-service-account \
  --member=serviceAccount:your-project-number-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Deploy with secret
gcloud run deploy month-end-close-api \
  --source . \
  --region us-central1 \
  --set-secrets=FIREBASE_SERVICE_ACCOUNT=/secrets/firebase-service-account:latest
```

**Method 2: Use Environment Variable (Simpler)**
```bash
# Convert JSON to base64
FIREBASE_JSON=$(cat firebase-service-account.json | base64)

# Deploy with env var
gcloud run deploy month-end-close-api \
  --source . \
  --region us-central1 \
  --set-env-vars FIREBASE_SERVICE_ACCOUNT_JSON=$FIREBASE_JSON
```

Then update `auth_service.py` to read from env var:
```python
import os
import json
import base64

# In auth_service.py
firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
if firebase_json:
    cred_dict = json.loads(base64.b64decode(firebase_json))
    cred = credentials.Certificate(cred_dict)
```

### Step 5: Test Firebase Authentication

```bash
# Test locally
cd adk-orchestrator
python3 -c "
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate('./firebase-service-account.json')
firebase_admin.initialize_app(cred)
print('✅ Firebase initialized successfully!')
"
```

---

## Quick Reference: What You Need

### For API Key Auth Only (Simplest):
```bash
# .env file
API_KEYS=your-generated-api-key
# FIREBASE_SERVICE_ACCOUNT=  # Leave commented out
```

### For Firebase Auth:
```bash
# .env file
API_KEYS=your-generated-api-key
FIREBASE_SERVICE_ACCOUNT=./firebase-service-account.json
```

---

## Security Best Practices

### ⚠️ NEVER commit firebase-service-account.json to GitHub!

Add to `.gitignore`:
```bash
echo "firebase-service-account.json" >> .gitignore
echo "adk-orchestrator/firebase-service-account.json" >> .gitignore
```

### ✅ What to commit:
- `.env.example` (template without real values)
- Code files
- Documentation

### ❌ What NOT to commit:
- `.env` (contains secrets)
- `firebase-service-account.json` (contains credentials)
- Any file with API keys or passwords

---

## Troubleshooting

### Error: "Could not load Firebase credentials"

**Solution 1:** Use API key authentication instead
```bash
# Comment out in .env
# FIREBASE_SERVICE_ACCOUNT=./firebase-service-account.json
```

**Solution 2:** Check file path
```bash
# Make sure file exists
ls -la adk-orchestrator/firebase-service-account.json

# Check .env path is correct
cat adk-orchestrator/.env | grep FIREBASE
```

### Error: "Permission denied"

**Solution:** Grant Cloud Run service account access
```bash
# Get service account email
gcloud run services describe month-end-close-api \
  --region us-central1 \
  --format='value(spec.template.spec.serviceAccountName)'

# Grant Firebase Admin role
gcloud projects add-iam-policy-binding your-project-id \
  --member=serviceAccount:SERVICE_ACCOUNT_EMAIL \
  --role=roles/firebase.admin
```

---

## Summary

### For Quick Deployment (Recommended):
1. **Skip Firebase** - Just use API key authentication
2. Generate API key: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
3. Add to `.env`: `API_KEYS=your-key`
4. Deploy!

### For Production with User Management:
1. Create Firebase project
2. Enable Email/Password authentication
3. Download service account JSON
4. Add to Cloud Run as secret
5. Deploy!

**Most users should start with API key auth and add Firebase later if needed.**
