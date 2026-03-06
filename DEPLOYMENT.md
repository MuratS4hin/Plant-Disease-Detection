# Plant Disease Detection - Deployment Guide

## 🐳 Docker Deployment

### Local Development with Docker

1. **Test Backend Locally**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Visit: http://localhost:8000/docs for API documentation

2. **Run with Docker Compose**
```bash
# From project root
docker-compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000

## 🚀 Deploy to Render.com

### Step 1: Prepare Your Repository

1. Push your code to GitHub:
```bash
git init
git add .
git commit -m "Initial commit with FastAPI backend and React frontend"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### Step 2: Deploy Backend on Render

1. **Go to [Render.com](https://render.com)** and sign in
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the backend service:
   - **Name**: `plant-disease-backend` (or your choice)
   - **Region**: Choose closest to your users
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free (or paid for better performance)

5. Click **"Create Web Service"**

6. Wait for deployment to complete. Note your backend URL:
   - Example: `https://plant-disease-backend.onrender.com`

### Step 3: Deploy Frontend on Render

1. Click **"New +"** → **"Web Service"** again
2. Connect the same GitHub repository
3. Configure the frontend service:
   - **Name**: `plant-disease-frontend`
   - **Region**: Same as backend
   - **Root Directory**: Leave blank (or `.`)
   - **Environment**: `Docker`
   - **Dockerfile Path**: `Dockerfile`
   - **Instance Type**: Free (or paid)

4. **Add Environment Variable**:
   - Key: `VITE_API_URL`
   - Value: `https://plant-disease-backend.onrender.com/predict` (use your actual backend URL)

5. Click **"Create Web Service"**

### Step 4: Alternative - Static Site for Frontend

For better performance and free hosting, deploy frontend as a Static Site:

1. Click **"New +"** → **"Static Site"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `plant-disease-app`
   - **Root Directory**: Leave blank
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`

4. **Add Environment Variable**:
   - Key: `VITE_API_URL`
   - Value: `https://plant-disease-backend.onrender.com/predict`

5. Click **"Create Static Site"**

### Step 5: Update CORS Settings

After deployment, update the backend CORS configuration:

In `backend/main.py`, update the allowed origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://plant-disease-app.onrender.com",  # Your frontend URL
        "http://localhost:3000",  # For local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit and push the changes - Render will auto-deploy.

## 🔧 Environment Variables

### Backend (.env in backend/)
```env
PORT=8000
```

### Frontend (.env in root)
```env
VITE_API_URL=https://your-backend-url.onrender.com/predict
```

## 📝 Important Notes

1. **Free Tier Limitations on Render**:
   - Services spin down after 15 minutes of inactivity
   - First request may take 30-60 seconds (cold start)
   - Consider paid tier for production

2. **Update Your Model**:
   - Replace the placeholder logic in `backend/main.py`
   - Add your trained model files
   - Update `requirements.txt` with ML dependencies (tensorflow, pytorch, etc.)

3. **File Size Limits**:
   - Current limit: 10MB per image
   - Adjust in `backend/main.py` if needed

4. **Security**:
   - Update CORS origins in production
   - Add authentication if needed
   - Use HTTPS only

## 🧪 Testing Your Deployment

1. Visit your frontend URL
2. Upload a test plant image
3. Check the response in the Output section
4. Monitor logs in Render dashboard if errors occur

## 📦 Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile          # Backend Docker config
├── src/
│   ├── App.tsx             # React main component
│   └── App.css             # Styles
├── Dockerfile              # Frontend Docker config
├── nginx.conf              # Nginx configuration
├── docker-compose.yml      # Local development
└── DEPLOYMENT.md           # This file
```

## 🔄 Continuous Deployment

Render automatically deploys when you push to your main branch:

```bash
git add .
git commit -m "Update model"
git push origin main
```

Your changes will be live in a few minutes!

## 🆘 Troubleshooting

### Backend not responding
- Check Render logs in the dashboard
- Verify environment variables
- Ensure PORT is correctly set

### CORS errors
- Update allowed origins in `backend/main.py`
- Redeploy backend after changes

### Frontend can't reach backend
- Check VITE_API_URL environment variable
- Verify backend URL is correct
- Check network tab in browser dev tools

## 📞 Support

For issues with:
- **Render deployment**: Check [Render docs](https://render.com/docs)
- **FastAPI**: Check [FastAPI docs](https://fastapi.tiangolo.com/)
- **React/Vite**: Check [Vite docs](https://vitejs.dev/)
