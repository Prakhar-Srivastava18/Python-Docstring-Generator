from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.models import CodeRequest, CodeResponse
from src.agent import generate_docstrings
import os

app = FastAPI(title="Docstring Generation Agent")

@app.post("/api/generate", response_model=CodeResponse)
async def generate(request: CodeRequest):
    if len(request.source_code) > 100000: 
        raise HTTPException(status_code=413, detail="Payload too large. Please process smaller files.")
        
    documented_code = generate_docstrings(request.source_code)
    
    if "Error:" in documented_code:
        return CodeResponse(documented_code=documented_code, message="Failed or empty input.")
        
    return CodeResponse(documented_code=documented_code, message="Docstrings generated successfully!")

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_path = os.path.join(base_dir, "frontend")

app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))
