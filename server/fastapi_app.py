from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.fastapi_routes import router as routes_router
from server.fastapi_auth import oauth2_scheme

app = FastAPI()

origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root_route():
    return {"message": "FastAPI MongoDB API"}

# attach routers
app.include_router(routes_router)

# you'd run it with: uvicorn server.fastapi_app:app --reload