"""
Project Prometheus - AI Social Behavior Simulation Platform
FastAPI Application Entry Point
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.rest import router as rest_router
from api.websockets import router as ws_router

app = FastAPI(
    title="Project Prometheus",
    description="AI Social Behavior Simulation Platform",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rest_router, prefix="/api/v1")
app.include_router(ws_router)

@app.get("/")
async def root():
    return {"message": "Project Prometheus - AI Social Behavior Simulation Platform"}

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    uvicorn.run("main:app", host=host, port=port, reload=debug)