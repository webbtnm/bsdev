from fastapi import APIRouter, Depends, HTTPException, FastAPI
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, OAuthFlowPassword
from fastapi.security import OAuth2, OAuth2PasswordBearer
from pydantic import BaseModel
from passlib.context import CryptContext
from db.mongo import db

app = FastAPI()

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(self, tokenUrl: str, scheme_name: str = None, scopes: dict = None, auto_error: bool = True):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password=OAuthFlowPassword(tokenUrl=tokenUrl, scopes=scopes))
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/api/token")

class UserCreate(BaseModel):
    username: str
    password: str
    telegram_contact: str | None = None

class UserOut(BaseModel):
    id: str
    username: str
    telegram_contact: str | None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = await db.users.find_one({"token": token})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

@router.post("/api/register")
async def register_user(user: UserCreate):
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_password = pwd_context.hash(user.password)
    new_user = {"username": user.username, "password": hashed_password, "telegram_contact": user.telegram_contact}
    result = await db.users.insert_one(new_user)
    return {"message": "Registration successful", "user": {"id": str(result.inserted_id), **new_user}}

@router.post("/api/login")
async def login_user(user: UserCreate):
    found_user = await db.users.find_one({"username": user.username})
    if not found_user or not pwd_context.verify(user.password, found_user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return {"message": "Login successful", "user": {"id": str(found_user["_id"]), **found_user}}

@router.post("/api/logout")
async def logout_user(token: str = Depends(oauth2_scheme)):
    user = await db.users.find_one({"token": token})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    await db.users.update_one({"_id": user["_id"]}, {"$unset": {"token": ""}})
    return {"message": "Logout successful"}

app.include_router(router)