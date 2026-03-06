from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from PIL import Image
import io
import os

app = FastAPI(title="Plant Disease Detection API")

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
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and validate image
        contents = await image.read()
        
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if len(contents) > max_size:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        try:
            img = Image.open(io.BytesIO(contents))
            width, height = img.size
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # TODO: Add your model inference here
        # Example placeholder response:
        result = {
            "status": "success",
            "filename": image.filename,
            "image_size": {
                "width": width,
                "height": height
            },
            "prediction": {
                "disease": "Healthy",  # Replace with actual prediction
                "confidence": 0.95,     # Replace with actual confidence
                "description": "Your plant appears to be healthy!"
            },
            "message": "Analysis complete. Replace this endpoint logic with your trained model."
        }
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
