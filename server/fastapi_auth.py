from fastapi import APIRouter, Depends, HTTPException, FastAPI, Request
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, OAuthFlowPassword
from fastapi.security import OAuth2, OAuth2PasswordBearer
from pydantic import BaseModel
from passlib.context import CryptContext
from db.firestore import db
from datetime import timedelta, datetime
from jose import JWTError, jwt
from bson import ObjectId
from fastapi.responses import JSONResponse
import logging
from google.cloud.firestore import AsyncClient
from google.cloud import firestore


app = FastAPI()

router = APIRouter(tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "your_secret_key"  # Ensure this is properly set
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    logging.info(f"Token received: {token}")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"token": token})
    try:
        token = token.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logging.info(f"Payload decoded: {payload}")
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user_ref = db.collection("users").document(user_id)
        user = user_ref.get()
        if not user.exists:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        logging.info(f"User found: {user.to_dict()}")
        user_data = user.to_dict()
        user_data["_id"] = user.id
        return user_data
    except JWTError as e:
        logging.error(f"JWTError: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/api/register")
def register_user(user: UserCreate):
    users_ref = db.collection("users")
    existing_users = users_ref.where("username", "==", user.username).stream()
    for user_doc in existing_users:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = pwd_context.hash(user.password)
    new_user = {
        "username": user.username,
        "password": hashed_password,
        "telegram_contact": user.telegram_contact
    }
    result = users_ref.add(new_user)
    document_ref = result[1]  # Extract the document reference
    return {
        "message": "Registration successful",
        "user": {
            "id": document_ref.id,
            "username": new_user["username"],
            "telegram_contact": new_user.get("telegram_contact")
        }
    }

@router.post("/api/login")
def login_user(user: UserCreate):
    users_ref = db.collection("users")
    found_users = users_ref.where("username", "==", user.username).stream()
    found_user = None
    for user_doc in found_users:
        found_user = user_doc.to_dict()
        found_user["_id"] = user_doc.id
        break
    if not found_user or not pwd_context.verify(user.password, found_user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(found_user["_id"])}, expires_delta=access_token_expires
    )
    user_ref = db.collection("users").document(found_user["_id"])
    user_ref.update({"token": access_token})
    response = JSONResponse(
        content={
            "message": "Login successful",
            "user": {
                "id": str(found_user["_id"]),
                "username": found_user["username"],
                "telegram_contact": found_user.get("telegram_contact")
            }
        }
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="strict",
        secure=True
    )
    return response

@router.post("/api/token")
def token_endpoint(user: UserCreate):
    logging.info(f"Received token request for user: {user.username}")
    users_ref = db.collection("users")
    found_users = users_ref.where("username", "==", user.username).stream()
    found_user = None
    for user_doc in found_users:
        found_user = user_doc.to_dict()
        found_user["_id"] = user_doc.id
        break
    if not found_user:
        logging.warning("User not found.")
    elif not pwd_context.verify(user.password, found_user["password"]):
        logging.warning("Password verification failed.")
    if not found_user or not pwd_context.verify(user.password, found_user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(found_user["_id"])}, expires_delta=access_token_expires
    )
    user_ref = db.collection("users").document(found_user["_id"])
    user_ref.update({"token": access_token})
    response = JSONResponse(
        content={
            "message": "Token endpoint successful",
            "user": {
                "id": str(found_user["_id"]),
                "username": found_user["username"],
                "telegram_contact": found_user.get("telegram_contact")
            }
        }
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="strict",
        secure=True
    )
    return response

@router.post("/api/logout")
def logout_user(request: Request, current_user: dict = Depends(get_current_user)):
    user_ref = db.collection("users").document(current_user["_id"])
    user_ref.update({"token": firestore.DELETE_FIELD})
    response = JSONResponse(content={"message": "Logout successful"})
    response.delete_cookie("access_token")
    return response

app.include_router(router)