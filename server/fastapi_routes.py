from fastapi import APIRouter, HTTPException, Depends, Request
from passlib.context import CryptContext
from pydantic import BaseModel
from bson import ObjectId
from db.firestore import db
from server.fastapi_auth import get_current_user, oauth2_scheme, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
import logging
from google.cloud.firestore import AsyncClient
import os
from dotenv import load_dotenv

load_dotenv()

# Use credentials from the .env file
credentials_path = os.getenv("FIRESTORE_CREDENTIALS")
firestore_client = AsyncClient.from_service_account_json(credentials_path)

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
def get_books():
    books_list = []
    books_ref = db.collection("books")
    for doc in books_ref.stream():
        b = doc.to_dict()
        books_list.append({
            "id": doc.id,
            "ownerId": b.get("ownerId"),
            "title": b["title"],
            "author": b["author"],
            "description": b.get("description", "")
        })
    return books_list

@router.post("/api/books")
def create_book(book: Book, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    new_book = {**book.dict(), "ownerId": current_user["_id"]}
    books_ref = db.collection("books")
    result = books_ref.add(new_book)
    document_ref = result[1]  # Extract the document reference
    return {"id": document_ref.id, **new_book}

@router.delete("/api/books/{book_id}")
def delete_book(book_id: str):
    book_ref = db.collection("books").document(book_id)
    book = book_ref.get()
    if not book.exists:
        raise HTTPException(status_code=404, detail="Book not found.")
    book_ref.delete()
    return {"message": "Book deleted"}

@router.post("/api/shelves")
def create_shelf(shelf: Shelf, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    new_shelf = {**shelf.dict(), "ownerId": current_user["_id"]}
    shelves_ref = db.collection("shelves")
    result = shelves_ref.add(new_shelf)
    document_ref = result[1]  # Extract the document reference
    return {"id": document_ref.id, **new_shelf}

@router.get("/api/shelves/{shelf_id}")
def get_shelf(shelf_id: str, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    shelf_ref = db.collection("shelves").document(shelf_id)
    shelf = shelf_ref.get()
    if not shelf.exists:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    shelf_data = shelf.to_dict()
    if not shelf_data["public"] and shelf_data["ownerId"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    return {
        "id": shelf.id,
        "name": shelf_data["name"],
        "description": shelf_data.get("description", ""),
        "public": shelf_data["public"],
        "ownerId": shelf_data["ownerId"]
    }

@router.post("/api/shelves/{shelf_id}/members")
def add_shelf_member(shelf_id: str, user_id: str, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    shelf_ref = db.collection("shelves").document(shelf_id)
    shelf = shelf_ref.get()
    if not shelf.exists:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    shelf_data = shelf.to_dict()
    if shelf_data["ownerId"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    new_member = {"shelfId": shelf_id, "userId": user_id}
    members_ref = db.collection("shelf_members")
    result = members_ref.add(new_member)
    return {"id": result.id, **new_member}

@router.get("/api/shelves/{shelf_id}/members")
def get_shelf_members(shelf_id: str, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    shelf_ref = db.collection("shelves").document(shelf_id)
    shelf = shelf_ref.get()
    if not shelf.exists:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    shelf_data = shelf.to_dict()
    if not shelf_data["public"] and shelf_data["ownerId"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    members_ref = db.collection("shelf_members")
    members = members_ref.where("shelfId", "==", shelf_id).stream()
    return [{"id": member.id, "shelfId": member.to_dict()["shelfId"], "userId": member.to_dict()["userId"]} for member in members]

@router.delete("/api/shelves/{shelf_id}/members/{member_id}")
def delete_shelf_member(shelf_id: str, member_id: str, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    shelf_ref = db.collection("shelves").document(shelf_id)
    shelf = shelf_ref.get()
    if not shelf.exists:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    shelf_data = shelf.to_dict()
    if shelf_data["ownerId"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    member_ref = db.collection("shelf_members").document(member_id)
    member = member_ref.get()
    if not member.exists:
        raise HTTPException(status_code=404, detail="Member not found.")
    member_ref.delete()
    return {"message": "Member deleted"}

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

# Remove or comment out these lines:
# @router.post("/api/register")
# async def register_user(user: UserCreate):
#     raise HTTPException(status_code=400, detail="Use /api/register from fastapi_auth")

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

@router.get("/api/shelves/{shelf_id}/books")
def get_shelf_books(shelf_id: str, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    shelf_ref = db.collection("shelves").document(shelf_id)
    shelf = shelf_ref.get()
    if not shelf.exists:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    shelf_data = shelf.to_dict()
    if not shelf_data["public"] and shelf_data["ownerId"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    books_ref = db.collection("shelf_books")
    books = books_ref.where("shelfId", "==", shelf_id).stream()
    return [{"id": book.id, "bookId": book.to_dict()["bookId"], "ownerId": book.to_dict()["ownerId"]} for book in books]

@router.post("/api/shelves/{shelf_id}/books")
def add_book_to_shelf(shelf_id: str, book_id: str, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    shelf_ref = db.collection("shelves").document(shelf_id)
    shelf = shelf_ref.get()
    if not shelf.exists:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    shelf_data = shelf.to_dict()
    if shelf_data["ownerId"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    # Check if the book belongs to the current user
    book_ref = db.collection("books").document(book_id)
    book = book_ref.get()
    if not book.exists:
        raise HTTPException(status_code=404, detail="Book not found.")
    book_data = book.to_dict()
    if book_data.get("ownerId") != current_user["_id"]:
        raise HTTPException(status_code=403, detail="You can only add your own books to the shelf.")
    # Add the book to the shelf
    new_book = {"shelfId": shelf_id, "bookId": book_id, "ownerId": current_user["_id"]}
    books_ref = db.collection("shelf_books")
    result = books_ref.add(new_book)
    document_ref = result[1]  # Extract the document reference
    return {"id": document_ref.id, **new_book}

@router.delete("/api/shelves/{shelf_id}/books/{book_id}")
def delete_book_from_shelf(shelf_id: str, book_id: str, current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    shelf_ref = db.collection("shelves").document(shelf_id)
    shelf = shelf_ref.get()
    if not shelf.exists:
        raise HTTPException(status_code=404, detail="Shelf not found.")
    shelf_data = shelf.to_dict()
    if shelf_data["ownerId"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized.")
    # Check if the book is associated with the shelf in the shelf_books collection
    shelf_books_ref = db.collection("shelf_books")
    shelf_book_query = shelf_books_ref.where("shelfId", "==", shelf_id).where("bookId", "==", book_id).stream()
    shelf_book = next(shelf_book_query, None)
    if not shelf_book:
        raise HTTPException(status_code=400, detail="Book does not belong to this shelf.")
    # Delete the association
    shelf_books_ref.document(shelf_book.id).delete()
    return {"message": "Book deleted from shelf"}