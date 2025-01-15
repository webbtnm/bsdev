from fastapi import APIRouter, HTTPException, Depends, Request
from server.fastapi_auth import get_current_user
from pydantic import BaseModel
import logging
from db.firestore import db

router = APIRouter()

class UserProfileUpdate(BaseModel):
    telegramContact: str | None = None

class UserOut(BaseModel):
    id: str
    username: str
    telegram_contact: str | None

@router.patch("/api/user/profile")
def update_user_profile(profile: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    update_data = {k: v for k, v in profile.dict().items() if v is not None}
    user_ref = db.collection("users").document(current_user["_id"])
    user_ref.update(update_data)
    return {"message": "Profile updated"}

@router.get("/api/user/profile", response_model=UserOut)
def get_user_profile(request: Request, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    return {
        "id": str(current_user["_id"]),
        "username": current_user["username"],
        "telegram_contact": current_user.get("telegram_contact")
    }

@router.get("/api/user/books")
def get_user_books(current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    logging.info(f"Current user: {current_user}")
    books_list = []
    books_ref = db.collection("books")
    for b in books_ref.where("ownerId", "==", current_user["_id"]).stream():
        books_list.append({
            "id": b.id,
            "title": b.to_dict()["title"],
            "author": b.to_dict()["author"],
            "description": b.to_dict().get("description", "")
        })
    return books_list

@router.get("/api/user/shelves")
def get_user_shelves(current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    shelves_list = []
    shelves_ref = db.collection("shelves")
    for s in shelves_ref.where("ownerId", "==", current_user["_id"]).stream():
        shelves_list.append({
            "id": s.id,
            "name": s.to_dict()["name"],
            "description": s.to_dict().get("description", ""),
            "public": s.to_dict()["public"]
        })
    return shelves_list