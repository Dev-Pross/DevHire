from fastapi import FastAPI
from database.db_engine import Base, engine
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("db schema created!!")
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"message": "DevHire Python API is live"}


    
