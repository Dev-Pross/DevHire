from fastapi import FastAPI
from main.routes.progress_route import progress_router as progress_router 
from database.db_engine import Base, engine
from contextlib import asynccontextmanager
from main.routes.cookie_receiver import router as cookie_router
from main.routes.list_jobs import router as list_jobs
from main.routes.apply_jobs import router as apply_jobs
from main.routes.debug_routes import router as debug_router
from fastapi.middleware.cors import CORSMiddleware
from main.routes.get_resume import router as tailor
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("db schema created!!")
    yield


app = FastAPI(lifespan=lifespan)
app.state.job_progress = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://ibdbgaedlhhpekneidifacdbjnpacfdd",  # Your extension ID
        "chrome-extension://*",  # Allow any Chrome extension (less secure)
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "https://dev-hire-znlr.vercel.app"],  # or ["http://localhost"] for strict control
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cookie_router)
app.include_router(list_jobs)
app.include_router(apply_jobs)
app.include_router(progress_router)
app.include_router(debug_router)
app.include_router(tailor)

@app.get("/")
def root():
    return {"message": "DevHire Python API is live"}


    
