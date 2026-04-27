from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from PIL import Image
import io
import os
from pathlib import Path

try:
    from backend.predict import predict_image
except ModuleNotFoundError:
    from predict import predict_image

app = FastAPI(title="Plant Disease Detection API")

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST_DIR = BASE_DIR / "dist"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

if (FRONTEND_DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")), name="assets")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    index_file = FRONTEND_DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Plant Disease Detection API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/predict")
async def predict(image: UploadFile = File(...)):
    """
    Endpoint to receive plant image and return disease prediction.
    Replace the logic below with your actual model inference.
    """
    try:
        # Validate file type
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and validate image
        contents = await image.read()
        
        # Validate file size (10MB limit)
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        try:
            img = Image.open(io.BytesIO(contents))
            width, height = img.size
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        prediction = predict_image(img)

        return {
            "status": "success",
            "filename": image.filename,
            "image_size": {
                "width": width,
                "height": height
            },
            "prediction": prediction,
            "message": "Analysis complete."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend(full_path: str):
    if not FRONTEND_DIST_DIR.exists():
        raise HTTPException(status_code=503, detail="Frontend build not found")

    requested_file = FRONTEND_DIST_DIR / full_path
    if full_path and requested_file.is_file():
        return FileResponse(str(requested_file))

    index_file = FRONTEND_DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))

    raise HTTPException(status_code=404, detail="Not Found")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app_import_path = "main:app" if __package__ in (None, "") else "backend.main:app"
    uvicorn.run(app_import_path, host="0.0.0.0", port=port, reload=True)
