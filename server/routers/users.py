from fastapi import APIRouter, HTTPException, Depends, Request
from server.fastapi_auth import get_current_user
from db.firestore import db
import logging
from server.models import UserOut

router = APIRouter(tags=["users"])

@router.get("/api/user/profile", response_model=UserOut)
def get_user_profile(request: Request, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    return {
        "id": str(current_user["_id"]),
        "username": current_user["username"],
        "telegram_contact": current_user.get("telegram_contact")
    } 