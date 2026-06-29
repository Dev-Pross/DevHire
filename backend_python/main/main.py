from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# Import active routes
from main.routes.debug_routes import router as debug_router
from main.routes.logout import logout_route
from main.routes.portfolio_generator import router as portfolio
from main.routes.get_resume import router as tailor
from main.routes.jobs_api import router as jobs_api
from main.routes.auth_api import router as auth_api

from config import redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure Redis connection works
    if redis_client:
        try:
            redis_client.ping()
            print("🚀 Successfully connected to Redis.")
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}")
    else:
        print("⚠️ No Redis URL provided, running without Redis (SSE won't work).")
    
    yield
    
    # Shutdown
    if redis_client:
        redis_client.close()
        print("🛑 Redis connection closed.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://ibdbgaedlhhpekneidifacdbjnpacfdd",  # Extension
        "chrome-extension://*",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "https://dev-hire-znlr.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# New workflow routes
app.include_router(jobs_api)
app.include_router(auth_api)

# Retained stateless routes
app.include_router(debug_router)
app.include_router(tailor)
app.include_router(logout_route)
app.include_router(portfolio)

@app.get("/")
def root():
    return {"message": "DevHire Serverless Python API is live"}
