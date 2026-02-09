# Deploying Todo Chatbot to Hugging Face Spaces

## Overview

We deploy **2 Hugging Face Spaces** (both free):
1. **Backend** — FastAPI API with in-memory storage (no Dapr/Kafka needed)
2. **Frontend** — Next.js web UI that connects to the backend Space

---

## Step 1: Deploy the Backend Space

### 1a. Create the Space
1. Go to **https://huggingface.co/new-space**
2. Fill in:
   - **Space name:** `todo-chatbot-backend`
   - **License:** MIT
   - **SDK:** Select **Docker**
   - **Hardware:** Free (CPU basic)
3. Click **Create Space**

### 1b. Push the backend code
Open your terminal and run these commands:

```bash
# Clone the empty HF Space
git clone https://huggingface.co/spaces/YOUR_USERNAME/todo-chatbot-backend
cd todo-chatbot-backend

# Copy files from your project
# (adjust the path to your project location)
cp -r "E:/AI classes/phase_5/services/backend/src" ./src
cp "E:/AI classes/phase_5/deploy/huggingface/backend/requirements.txt" ./requirements.txt
cp "E:/AI classes/phase_5/deploy/huggingface/backend/README.md" ./README.md
cp "E:/AI classes/phase_5/deploy/huggingface/backend/Dockerfile" ./Dockerfile

# Push to Hugging Face
git add -A
git commit -m "Deploy backend API"
git push
```

### 1c. Verify
- Wait 2-3 minutes for the build
- Visit: `https://YOUR_USERNAME-todo-chatbot-backend.hf.space/docs`
- You should see the **Swagger API documentation**
- Test the health endpoint: `https://YOUR_USERNAME-todo-chatbot-backend.hf.space/health`

---

## Step 2: Deploy the Frontend Space

### 2a. Create the Space
1. Go to **https://huggingface.co/new-space**
2. Fill in:
   - **Space name:** `todo-chatbot-frontend`
   - **License:** MIT
   - **SDK:** Select **Docker**
   - **Hardware:** Free (CPU basic)
3. Click **Create Space**

### 2b. Push the frontend code
```bash
# Clone the empty HF Space
git clone https://huggingface.co/spaces/YOUR_USERNAME/todo-chatbot-frontend
cd todo-chatbot-frontend

# Copy files from your project
cp -r "E:/AI classes/phase_5/services/frontend/." ./
cp "E:/AI classes/phase_5/deploy/huggingface/frontend/README.md" ./README.md
cp "E:/AI classes/phase_5/deploy/huggingface/frontend/Dockerfile" ./Dockerfile

# IMPORTANT: Update the API URL in the Dockerfile to your actual backend Space URL
# Open Dockerfile and replace the NEXT_PUBLIC_API_URL with your backend URL:
# ARG NEXT_PUBLIC_API_URL=https://YOUR_USERNAME-todo-chatbot-backend.hf.space/api

# Push to Hugging Face
git add -A
git commit -m "Deploy frontend UI"
git push
```

### 2c. Verify
- Wait 3-5 minutes for the build (Next.js build takes longer)
- Visit: `https://YOUR_USERNAME-todo-chatbot-frontend.hf.space`
- You should see the **Todo Chatbot web interface**

---

## Quick Test

Once both Spaces are running:

```bash
# Test backend API directly
curl -X POST https://YOUR_USERNAME-todo-chatbot-backend.hf.space/api/tasks \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test-user" \
  -d '{"title": "My first task", "priority": "high"}'

# List tasks
curl https://YOUR_USERNAME-todo-chatbot-backend.hf.space/api/tasks \
  -H "X-User-ID: test-user"
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Build fails | Check the **Logs** tab in HF Space settings |
| Frontend can't reach backend | Verify `NEXT_PUBLIC_API_URL` in frontend Dockerfile |
| Space sleeps after inactivity | Free Spaces sleep after ~15 min idle. Visit the URL to wake it. |
| CORS errors | Backend includes CORS middleware allowing all origins |

---

## Architecture on Hugging Face

```
User Browser
    ↓
Frontend Space (Next.js, port 7860)
    ↓ REST API calls
Backend Space (FastAPI, port 7860)
    ↓ In-memory state
MemoryStateStore (dict-backed)
```

**Note:** This deployment uses in-memory storage. Data is lost when the Space restarts.
For production persistence, use the full Kubernetes deployment with Dapr + PostgreSQL.
