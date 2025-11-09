# Railway Deployment Guide for Peerly

Complete guide to deploy the full-stack Peerly application on Railway.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Railway Project: Peerly                    │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Frontend   │  │   Backend    │  │     Qdrant       │  │
│  │ (React/Vite) │  │  (FastAPI)   │  │  (Vector DB)     │  │
│  │              │  │              │  │                  │  │
│  │  Port: 3000  │  │  Port: 8000  │  │  Port: 6333      │  │
│  │              │  │              │  │                  │  │
│  │  PUBLIC URL  │  │  PUBLIC URL  │  │  INTERNAL ONLY   │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                 │                    │            │
│         └─────────────────┴────────────────────┘            │
│              Railway Private Network                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Pre-Deployment Checklist

- [ ] GitHub repository ready
- [ ] Railway account created (sign up at https://railway.app)
- [ ] OpenAI API key ready
- [ ] Git repository pushed to GitHub
- [ ] All deployment files created (see below)

---

## 🚀 Quick Start

### Option 1: One-Click Deploy (Coming Soon)
Click the button below to deploy all services:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/...)

### Option 2: Manual Deployment (Detailed Below)

---

## 📦 Services Configuration

### Service 1: Backend (FastAPI + Python)

**Purpose**: API server for LaTeX review, compilation, and agent orchestration

**Configuration:**
- **Builder**: Dockerfile
- **Root Directory**: `/`
- **Port**: `8000` (auto-assigned by Railway)
- **Health Check**: `/api/health`
- **Restart Policy**: On failure (max 10 retries)

**Environment Variables:**
```bash
# OpenAI Configuration
OPENAI_API_KEY=<your-openai-api-key>
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.2

# Qdrant Configuration (use Railway internal URL)
QDRANT_URL=http://${{Qdrant.RAILWAY_PRIVATE_DOMAIN}}:6333
QDRANT_HOST=${{Qdrant.RAILWAY_PRIVATE_DOMAIN}}
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=technical_guidelines

# RAG Configuration
USE_RAG=true
USE_SEMANTIC_CACHE=false

# Agent Configuration
MAX_PARALLEL_AGENTS=3
AGENT_TIMEOUT=30

# CORS (add frontend URL after it's deployed)
CORS_ORIGINS=["https://${{Frontend.RAILWAY_PUBLIC_DOMAIN}}","http://localhost:5173"]

# Railway
RAILWAY_ENVIRONMENT=production
```

**Volumes:**
- `/tmp/latex-editor-project` - LaTeX source files
- `/tmp/latex-editor-output` - Compiled PDFs

---

### Service 2: Frontend (React + Vite)

**Purpose**: User interface for LaTeX editing and AI suggestions

**Configuration:**
- **Builder**: Nixpacks
- **Root Directory**: `/frontend`
- **Port**: `3000` (auto-assigned by Railway)
- **Build Command**: `npm install && npm run build`
- **Start Command**: `npm run start`

**Environment Variables:**
```bash
# Backend API URL (set after backend is deployed)
VITE_API_BASE_URL=https://${{Backend.RAILWAY_PUBLIC_DOMAIN}}
```

---

### Service 3: Qdrant (Vector Database)

**Purpose**: Store and retrieve RAG embeddings for writing guidelines

**Configuration:**
- **Builder**: Docker Image
- **Image**: `qdrant/qdrant:latest`
- **Port**: `6333`
- **Access**: Internal only (no public URL)

**Environment Variables:**
```bash
# None required - uses defaults
```

**Volumes:**
- `/qdrant/storage` - Persistent vector storage

---

## 🛠️ Step-by-Step Deployment

### Step 1: Create Railway Project

1. Go to https://railway.app
2. Click **"Login"** and authenticate with GitHub
3. Click **"New Project"**
4. Select **"Deploy from GitHub repo"**
5. Choose your `Peerly-Demo` repository
6. Railway will auto-detect the backend

### Step 2: Deploy Qdrant Service

1. In your project dashboard, click **"+ New"**
2. Select **"Database"** → Look for **"Qdrant"**
   - If available, click **"Add Qdrant"**
   - If not available, continue to Step 3

3. **Manual Qdrant Setup:**
   - Click **"+ New"** → **"Empty Service"**
   - Name it `Qdrant`
   - Go to **"Settings"** → **"Source"**
   - Click **"Deploy from Docker Image"**
   - Enter image: `qdrant/qdrant:latest`
   - Go to **"Variables"** → Add:
     ```
     PORT=6333
     ```
   - Go to **"Settings"** → **"Volumes"** → **"+ New Volume"**
   - Mount path: `/qdrant/storage`

4. **Important**: Do NOT generate a public domain for Qdrant (keep internal only)

### Step 3: Configure Backend Service

Railway should have auto-detected your backend. If not:

1. Click **"+ New"** → **"GitHub Repo"** → Select your repository
2. Name it `Backend`
3. Go to **"Settings"**:
   - Root Directory: `/` (leave empty or set to root)
   - Dockerfile Path: `Dockerfile`
   - Start Command: `uv run uvicorn main:app --host 0.0.0.0 --port $PORT`

4. Go to **"Variables"** → **"Raw Editor"** → Paste:
   ```bash
   OPENAI_API_KEY=<your-key-here>
   OPENAI_MODEL=gpt-4o-mini
   OPENAI_TEMPERATURE=0.2
   QDRANT_URL=http://${{Qdrant.RAILWAY_PRIVATE_DOMAIN}}:6333
   QDRANT_HOST=${{Qdrant.RAILWAY_PRIVATE_DOMAIN}}
   QDRANT_PORT=6333
   QDRANT_COLLECTION_NAME=technical_guidelines
   USE_RAG=true
   USE_SEMANTIC_CACHE=false
   MAX_PARALLEL_AGENTS=3
   AGENT_TIMEOUT=30
   RAILWAY_ENVIRONMENT=production
   ```

5. Go to **"Settings"** → **"Networking"** → **"Generate Domain"**
6. Copy the generated URL (e.g., `https://peerly-backend-production.up.railway.app`)

7. Add volumes:
   - Click **"Settings"** → **"Volumes"** → **"+ New Volume"**
   - Mount path: `/tmp/latex-editor-project`
   - Click **"+ New Volume"** again
   - Mount path: `/tmp/latex-editor-output`

### Step 4: Deploy Frontend Service

1. Click **"+ New"** → **"GitHub Repo"** → Select your repository again
2. Name it `Frontend`
3. Go to **"Settings"**:
   - Root Directory: `/frontend`
   - Build Command: (auto-detected)
   - Start Command: `npm run start`

4. Go to **"Variables"** → Add:
   ```bash
   VITE_API_BASE_URL=https://${{Backend.RAILWAY_PUBLIC_DOMAIN}}
   ```

5. Go to **"Settings"** → **"Networking"** → **"Generate Domain"**
6. Copy the frontend URL (e.g., `https://peerly-frontend-production.up.railway.app`)

### Step 5: Update Backend CORS

1. Go to **Backend** service → **"Variables"**
2. Add/Update:
   ```bash
   CORS_ORIGINS=["https://${{Frontend.RAILWAY_PUBLIC_DOMAIN}}","http://localhost:5173"]
   ```

3. Click **"Deploy"** to restart with new variables

### Step 6: Initialize Qdrant Collection

**Option A: Using Railway CLI**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Select the Backend service
railway service

# Run initialization
railway run python -c "from app.rag.vector_store import rag_service; import asyncio; asyncio.run(rag_service.initialize_collection())"
```

**Option B: Manual via API**

1. Wait for all services to deploy
2. Visit: `https://your-backend-url.railway.app/api/health`
3. The backend will auto-initialize Qdrant on first startup (if configured)

---

## ✅ Verification Steps

### 1. Backend Health Check
```bash
curl https://your-backend.railway.app/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Peerly Review API"
}
```

### 2. Frontend Access
- Visit: `https://your-frontend.railway.app`
- Open browser DevTools → Network tab
- Check for successful API calls to backend
- No CORS errors should appear

### 3. Full Integration Test
1. Open frontend
2. Load a LaTeX document
3. Click "Run Analysis"
4. Verify suggestions appear
5. Check backend logs in Railway dashboard

---

## 🔍 Monitoring & Debugging

### View Logs

**Railway Dashboard:**
1. Go to your service (Backend/Frontend)
2. Click **"Deployments"** tab
3. Click on latest deployment
4. View real-time logs

**Railway CLI:**
```bash
railway logs
```

### Common Issues

**Issue: CORS Error**
- **Solution**: Verify `CORS_ORIGINS` includes frontend URL
- Check backend logs for CORS configuration

**Issue: Qdrant Connection Failed**
- **Solution**: Verify `QDRANT_URL` uses Railway internal domain
- Should be: `http://${{Qdrant.RAILWAY_PRIVATE_DOMAIN}}:6333`
- NOT: `http://localhost:6333`

**Issue: Frontend Can't Reach Backend**
- **Solution**: Verify `VITE_API_BASE_URL` is set correctly
- Rebuild frontend after changing env vars

**Issue: Tectonic Not Found (Backend)**
- **Solution**: Dockerfile installs Tectonic correctly
- Check build logs for installation errors

**Issue: Out of Memory**
- **Solution**: Upgrade Railway plan or increase memory limits
- Check service settings for memory allocation

---

## 💰 Cost Estimation

### Railway Plans

| Plan | Price | Credits | Best For |
|------|-------|---------|----------|
| **Hobby** | $5/month | $5 usage | Development, low traffic |
| **Pro** | $20/month | $10 usage | Production, moderate traffic |
| **Team** | Custom | Custom | High traffic, team collaboration |

### Estimated Monthly Cost for Peerly

**Hobby Plan** ($5/month):
- 3 services running 24/7
- Low to moderate usage
- **Total**: ~$10-15/month ($5 plan + $5-10 usage)
- **Good for**: Personal use, demos, testing

**Pro Plan** ($20/month):
- 3 services running 24/7
- Higher traffic capacity
- Better resources per service
- **Total**: ~$25-35/month ($20 plan + $5-15 usage)
- **Good for**: Production apps, multiple users, professional use

**Recommendation**:
- Start with **Hobby Plan** for development/testing
- Upgrade to **Pro Plan** when deploying to production or expecting real users

### Usage Breakdown
- **Backend**: ~$3-5/month (CPU + Memory)
- **Frontend**: ~$2-3/month (Static serving + Node)
- **Qdrant**: ~$3-5/month (Memory + Storage)
- **Network**: ~$1-2/month (Egress traffic)

---

## 🔒 Security Best Practices

1. **Environment Variables**
   - Never commit `.env` files
   - Use Railway's built-in secrets management
   - Rotate API keys regularly

2. **Qdrant Access**
   - Keep Qdrant internal only (no public URL)
   - Use Railway's private network

3. **CORS Configuration**
   - Only allow your frontend domain
   - Remove localhost from production CORS

4. **API Keys**
   - Use separate OpenAI keys for dev/prod
   - Monitor usage in OpenAI dashboard

---

## 🔄 Continuous Deployment

Railway automatically deploys on git push:

```bash
# Make changes
git add .
git commit -m "feat: new feature"
git push origin main

# Railway automatically:
# 1. Detects changes
# 2. Builds services
# 3. Runs tests (if configured)
# 4. Deploys to production
```

**Deployment Triggers:**
- Push to `main` branch (default)
- Can configure different branches for different environments

**Rollback:**
1. Go to service → **"Deployments"**
2. Find previous successful deployment
3. Click **"Redeploy"**

---

## 📊 Environment-Specific Configurations

### Development Environment
```bash
RAILWAY_ENVIRONMENT=development
USE_RAG=false  # Skip RAG for faster iteration
USE_SEMANTIC_CACHE=false
OPENAI_MODEL=gpt-4o-mini  # Cheaper model
```

### Production Environment
```bash
RAILWAY_ENVIRONMENT=production
USE_RAG=true
USE_SEMANTIC_CACHE=true
OPENAI_MODEL=gpt-4o-mini  # Or gpt-4o for better quality
```

---

## 🆘 Support & Resources

- **Railway Documentation**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Railway Status**: https://status.railway.app
- **Peerly GitHub Issues**: [Your repo URL]

---

## 📝 Deployment Checklist

Before going live:

- [ ] All services deployed successfully
- [ ] Environment variables configured
- [ ] Public URLs generated for Frontend and Backend
- [ ] CORS configured correctly
- [ ] Qdrant collection initialized
- [ ] Health check passing
- [ ] Frontend loads without errors
- [ ] Can submit LaTeX and get suggestions
- [ ] Can compile to PDF
- [ ] Logs show no critical errors
- [ ] Monitoring set up (if using external tools)
- [ ] Backup strategy for Qdrant data (export collection)

---

## 🎯 Next Steps After Deployment

1. **Custom Domain** (Optional)
   - Add your own domain in Railway settings
   - Configure DNS records
   - Enable automatic HTTPS

2. **Monitoring**
   - Set up error tracking (Sentry, etc.)
   - Configure uptime monitoring
   - Set up alerts for failures

3. **Analytics**
   - Add analytics to frontend
   - Track usage patterns
   - Monitor API performance

4. **Scaling**
   - Monitor resource usage
   - Adjust service limits as needed
   - Consider caching strategies

---

## 📄 License

[Your License Here]

---

**Last Updated**: 2025-01-08
**Version**: 1.0.0
