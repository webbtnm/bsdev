from fastapi import APIRouter, HTTPException, Depends, Request
from passlib.context import CryptContext
from pydantic import BaseModel
from bson import ObjectId
from db.mongo import db
from server.fastapi_auth import get_current_user, oauth2_scheme, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
import logging

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()

class Book(BaseModel):
    title: str
    author: str
    description: str | None = None

class Shelf(BaseModel):
    name: str
    description: str | None = None
    public: bool = True

class UserProfileUpdate(BaseModel):
    telegramContact: str | None = None

class UserCreate(BaseModel):
    username: str
    password: str
    telegram_contact: str | None = None

class UserOut(BaseModel):
    id: str
    username: str
    telegram_contact: str | None

@router.get("/api/books")
async def get_books():
    books_list = []
    async for b in db.books.find():
        books_list.append({
            "id": str(b["_id"]),
            "title": b["title"],
            "author": b["author"],
            "description": b.get("description", "")
        })
    return books_list

@router.post("/api/books")
async def create_book(book: Book):
    result = await db.books.insert_one(book.dict())
    return {"id": str(result.inserted_id), **book.dict()}

@router.delete("/api/books/{book_id}")
async def delete_book(book_id: str):
    res = await db.books.delete_one({"_id": ObjectId(book_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found.")
    return {"message": "Book deleted"}

@router.post("/api/shelves")
async def create_shelf(shelf: Shelf, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    new_shelf = {**shelf.dict(), "ownerId": current_user["_id"]}
    result = await db.shelves.insert_one(new_shelf)
    return {"id": str(result.inserted_id), **new_shelf}

@router.get("/api/shelves/{shelf_id}")
async def get_shelf(shelf_id: str, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    shelf = await db.shelves.find_one({"_id": ObjectId(shelf_id)})
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    if not shelf["public"] and shelf["ownerId"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    return {
        "id": str(shelf["_id"]),
        "name": shelf["name"],
        "description": shelf.get("description", ""),
        "public": shelf["public"],
        "ownerId": str(shelf["ownerId"])
    }

@router.post("/api/shelves/{shelf_id}/members")
async def add_shelf_member(shelf_id: str, user_id: str, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    shelf = await db.shelves.find_one({"_id": ObjectId(shelf_id)})
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    if shelf["ownerId"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    new_member = {"shelfId": ObjectId(shelf_id), "userId": ObjectId(user_id)}
    result = await db.shelf_members.insert_one(new_member)
    return {"id": str(result.inserted_id), **new_member}

@router.get("/api/shelves/{shelf_id}/members")
async def get_shelf_members(shelf_id: str, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    shelf = await db.shelves.find_one({"_id": ObjectId(shelf_id)})
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    if not shelf["public"] and shelf["ownerId"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    members = await db.shelf_members.find({"shelfId": ObjectId(shelf_id)}).to_list(length=None)
    return [{"id": str(member["_id"]), "shelfId": str(member["shelfId"]), "userId": str(member["userId"])} for member in members]

@router.delete("/api/shelves/{shelf_id}/members/{member_id}")
async def delete_shelf_member(shelf_id: str, member_id: str, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    shelf = await db.shelves.find_one({"_id": ObjectId(shelf_id)})
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    if shelf["ownerId"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    result = await db.shelf_members.delete_one({"shelfId": ObjectId(shelf_id), "userId": ObjectId(member_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Member not found.")
    return {"message": "Member deleted"}

@router.patch("/api/user/profile")
async def update_user_profile(profile: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    update_data = {k: v for k, v in profile.dict().items() if v is not None}
    result = await db.users.update_one({"_id": ObjectId(current_user["_id"])}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"message": "Profile updated"}

@router.get("/api/user/profile", response_model=UserOut)
async def get_user_profile(request: Request, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    token = request.cookies.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "id": str(current_user["_id"]),
        "username": current_user["username"],
        "telegram_contact": current_user.get("telegram_contact")
    }

# Remove or comment out these lines:
# @router.post("/api/register")
# async def register_user(user: UserCreate):
#     raise HTTPException(status_code=400, detail="Use /api/register from fastapi_auth")

@router.get("/api/user/books")
async def get_user_books(current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    logging.info(f"Current user: {current_user}")
    books_list = []
    async for b in db.books.find({"ownerId": current_user["_id"]}):
        books_list.append({
            "id": str(b["_id"]),
            "title": b["title"],
            "author": b["author"],
            "description": b.get("description", "")
        })
    return books_list

@router.get("/api/user/shelves")
async def get_user_shelves(current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    shelves_list = []
    async for s in db.shelves.find({"ownerId": current_user["_id"]}):
        shelves_list.append({
            "id": str(s["_id"]),
            "name": s["name"],
            "description": s.get("description", ""),
            "public": s["public"]
        })
    return shelves_list