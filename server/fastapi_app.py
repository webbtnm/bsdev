from fastapi import FastAPI
from server.fastapi_routes import router as routes_router

app = FastAPI()

@app.get("/")
def root_route():
    return {"message": "FastAPI MongoDB API"}

# attach routers
app.include_router(routes_router)

# you'd run it with: uvicorn server.fastapi_app:app --reload