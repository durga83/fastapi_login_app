import sys
import os
from fastapi import FastAPI, Request, HTTPException
import uvicorn
from fastapi.responses import JSONResponse
from app.routes import user_routes
from app.database import engine
from app.models import SQLModel

# Add the root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = FastAPI()

# Register routes
app.include_router(user_routes.router)

# Create tables
def create_tables():
    SQLModel.metadata.create_all(engine)

@app.on_event("startup")
async def startup():
    create_tables()

@app.get("/")
def root():
    return {"status": "SUCCESS", "message": "API is running", "data": []}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
