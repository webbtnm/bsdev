from fastapi import APIRouter, HTTPException, Depends
from passlib.context import CryptContext
from pydantic import BaseModel
from bson import ObjectId
from ..db.mongo import db
from .fastapi_auth import get_current_user
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
    new_shelf = {**shelf.dict(), "ownerId": current_user["id"]}
    result = await db.shelves.insert_one(new_shelf)
    return {"id": str(result.inserted_id), **new_shelf}

@router.get("/api/shelves/{shelf_id}")
async def get_shelf(shelf_id: str, current_user: dict = Depends(get_current_user)):
    shelf = await db.shelves.find_one({"_id": ObjectId(shelf_id)})
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    if not shelf["public"] and shelf["ownerId"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    return shelf

@router.post("/api/shelves/{shelf_id}/members")
async def add_shelf_member(shelf_id: str, user_id: str, current_user: dict = Depends(get_current_user)):
    shelf = await db.shelves.find_one({"_id": ObjectId(shelf_id)})
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    if shelf["ownerId"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    new_member = {"shelfId": ObjectId(shelf_id), "userId": ObjectId(user_id)}
    result = await db.shelf_members.insert_one(new_member)
    return {"id": str(result.inserted_id), **new_member}

@router.get("/api/shelves/{shelf_id}/members")
async def get_shelf_members(shelf_id: str, current_user: dict = Depends(get_current_user)):
    shelf = await db.shelves.find_one({"_id": ObjectId(shelf_id)})
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    if not shelf["public"] and shelf["ownerId"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    members = await db.shelf_members.find({"shelfId": ObjectId(shelf_id)}).to_list(length=None)
    return members

@router.patch("/api/user/profile")
async def update_user_profile(profile: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in profile.dict().items() if v is not None}
    result = await db.users.update_one({"_id": ObjectId(current_user["id"])}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"message": "Profile updated"}

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