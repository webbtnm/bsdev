from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.fastapi_routes import router as routes_router
from server.fastapi_auth import router as auth_router  # Add this import
from starlette.middleware.base import BaseHTTPMiddleware
import logging

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

class CookieToHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        token = request.cookies.get("Authorization")
        if token:
            logging.info(f"Token from cookie: {token}")
            # Inject the cookie value as an 'Authorization' header
            request.headers.__dict__["_list"].append(
                (b"authorization", token.encode())
            )
        response = await call_next(request)
        return response

app.add_middleware(CookieToHeaderMiddleware)

@app.get("/")
def root_route():
    return {"message": "FastAPI MongoDB API"}

# attach routers
app.include_router(routes_router)
app.include_router(auth_router)  # Include auth router so /api/token and others are available

# you'd run it with: uvicorn server.fastapi_app:app --reload