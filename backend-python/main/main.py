from fastapi import FastAPI
# from backend-python import index

app = FastAPI()
# app.include_router(agent.router)

@app.get("/")
def root():
    return {"message": "DevHire Python API is live"}

# @app.get("/scrape")
# def index():
    
