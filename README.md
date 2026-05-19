# Plant Disease Detection - Pattern Recognition Project

A full-stack web application for detecting plant diseases using image analysis. Built for a master's degree project in Pattern Recognition at İTÜ.

## 🚀 Tech Stack

### Frontend
- **React 19** - UI framework
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Nginx** - Production web server

### Backend
- **FastAPI** - High-performance Python API framework
- **Pillow** - Image processing
- **Uvicorn** - ASGI server

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Render.com** - Deployment platform

## 📦 Quick Start

### Local Development (Without Docker)

**Frontend:**
```bash
npm install
npm run dev
# Visit http://localhost:5173
```

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt 
    OR 
python3 -m pip install -r requirements.txt
python3 main.py
# Plant Disease Detection - Pattern Recognition Project

**Dockerize:**
Run docker deamon
docker compose up --build -d

# For clean rebuild (if you get error try with this one)
docker compose down --rmi local && docker compose build --no-cache && docker compose up -d
