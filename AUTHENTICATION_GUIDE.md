# Authentication Guide

## Overview

The Smart Month-End Close system supports **two authentication methods**:

1. **Firebase Authentication** (Recommended for production)
2. **API Key Authentication** (Fallback/Development)

## Complete Feature Checklist

### ✅ IMPLEMENTED:

1. **User Authentication**
   - ✅ Firebase Auth integration (email/password)
   - ✅ API key fallback authentication
   - ✅ Development mode (no auth required)

2. **Multiple Document Upload**
   - ✅ `/upload` - Single file upload
   - ✅ `/upload-multiple` - Multiple files with auto-report

3. **BigQuery Integration**
   - ✅ Documents table
   - ✅ Structured data table
   - ✅ Embeddings table

4. **Embedding Generation**
   - ✅ Sentence transformers model
   - ✅ Column-aware chunking
   - ✅ Automatic embedding on upload

5. **Month-End Reports**
   - ✅ `/generate-report` endpoint
   - ✅ Summary statistics
   - ✅ Checklist completion
   - ✅ Recommendations

6. **Chatbot with Uploaded Data**
   - ✅ `/chat` endpoint
   - ✅ RAG-powered search
   - ✅ Firestore conversation history
   - ✅ Context-aware responses

### ❌ NOT IMPLEMENTED (Frontend):

- ❌ Sign Up UI (need to build frontend)
- ❌ Sign In UI (need to build frontend)
- ❌ Password reset UI

**Note**: Backend supports Firebase Auth, but you need to create the frontend forms.

## Firebase Authentication Setup

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or use existing
3. Enable **Authentication** → **Email/Password**

### 2. Get Service Account Key

1. Go to Project Settings → Service Accounts
2. Click "Generate New Private Key"
3. Save as `firebase-service-account.json`
4. Add to `.env`:
   ```
   FIREBASE_SERVICE_ACCOUNT=./firebase-service-account.json
   ```

### 3. Frontend Integration (Example)

```javascript
// Initialize Firebase in your frontend
import { initializeApp } from 'firebase/app';
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Sign Up
async function signUp(email, password) {
  const userCredential = await createUserWithEmailAndPassword(auth, email, password);
  const idToken = await userCredential.user.getIdToken();
  return idToken;
}

// Sign In
async function signIn(email, password) {
  const userCredential = await signInWithEmailAndPassword(auth, email, password);
  const idToken = await userCredential.user.getIdToken();
  return idToken;
}

// Use token in API calls
async function uploadFiles(files, idToken) {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  
  const response = await fetch('http://your-api/upload-multiple', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${idToken}`
    },
    body: formData
  });
  
  return response.json();
}
```

## API Key Authentication (Development)

### For Testing Without Firebase:

```bash
# In .env
ENVIRONMENT=development
API_KEYS=demo-key-12345
```

### Using API Key:

```bash
# With API key
curl -X POST http://localhost:8080/upload \
  -H "X-API-Key: demo-key-12345" \
  -F "file=@bank_statement.csv"

# In development mode (no auth required)
curl -X POST http://localhost:8080/upload \
  -F "file=@bank_statement.csv"
```

## Complete User Flow

### 1. User Signs Up (Frontend)

```
User enters email/password
  ↓
Frontend calls Firebase Auth createUser
  ↓
Firebase returns ID token
  ↓
Frontend stores token
```

### 2. User Logs In (Frontend)

```
User enters email/password
  ↓
Frontend calls Firebase Auth signIn
  ↓
Firebase returns ID token
  ↓
Frontend stores token
```

### 3. User Uploads Documents

```
User selects multiple CSV files
  ↓
Frontend sends POST /upload-multiple
  with Authorization: Bearer <token>
  ↓
Backend verifies token with Firebase
  ↓
Backend processes files:
  - Classifies each document
  - Extracts data to BigQuery
  - Generates embeddings
  - Updates checklist in Firestore
  ↓
Backend generates report
  ↓
Returns: {results, report}
```

### 4. User Chats with Data

```
User types question
  ↓
Frontend sends POST /chat
  with Authorization: Bearer <token>
  and message
  ↓
Backend:
  - Verifies user
  - Searches embeddings (RAG)
  - Generates response
  - Saves to Firestore
  ↓
Returns: {response, search_results}
```

## API Endpoints with Auth

All endpoints require authentication (Firebase token or API key):

### Upload Endpoints
- `POST /upload` - Single file
- `POST /upload-multiple` - Multiple files + report

### Data Endpoints
- `GET /checklist` - Get user's checklist
- `GET /data/{doc_type}` - Query BigQuery data
- `POST /search` - Search with RAG
- `POST /generate-report` - Generate report
- `POST /chat` - Chat with data

### Auth Endpoints
- `GET /me` - Get current user info
- `GET /health` - Health check (no auth)

## Testing Authentication

### Test with Firebase Token:

```bash
# Get token from Firebase (use frontend or Firebase CLI)
TOKEN="your-firebase-id-token"

curl -X POST http://localhost:8080/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@bank_statement.csv"
```

### Test with API Key:

```bash
curl -X POST http://localhost:8080/upload \
  -H "X-API-Key: demo-key-12345" \
  -F "file=@bank_statement.csv"
```

### Test in Development Mode:

```bash
# No auth required
curl -X POST http://localhost:8080/upload \
  -F "file=@bank_statement.csv"
```

## Security Best Practices

1. **Never commit** `firebase-service-account.json`
2. **Use HTTPS** in production
3. **Set ENVIRONMENT=production** in Cloud Run
4. **Rotate API keys** regularly
5. **Enable Firebase email verification**
6. **Set up Firebase security rules**

## What You Need to Build (Frontend)

To complete the system, create:

1. **Sign Up Page**
   - Email input
   - Password input
   - Submit button
   - Calls Firebase `createUserWithEmailAndPassword`

2. **Sign In Page**
   - Email input
   - Password input
   - Submit button
   - Calls Firebase `signInWithEmailAndPassword`

3. **Upload Page**
   - Multiple file selector
   - Upload button
   - Progress indicator
   - Sends files with Authorization header

4. **Chat Interface**
   - Message input
   - Chat history display
   - Sends messages with Authorization header

## Summary

✅ **Backend is 100% complete** with:
- Firebase Auth integration
- Multiple file upload
- BigQuery storage
- Embedding generation
- Report generation
- RAG-powered chatbot

❌ **Frontend needs**:
- Sign up/sign in forms
- File upload UI
- Chat interface

The backend is production-ready. You just need to build the frontend UI!
