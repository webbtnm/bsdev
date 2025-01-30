from fastapi import APIRouter, HTTPException, Depends
from server.fastapi_auth import get_current_user
from db.firestore import db
import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime
import uuid
from server.models import Book, CreateBookRequest, LitresUrlInput, LitresBookResponse

router = APIRouter(tags=["books"])

@router.get("/api/books")
def get_books():
    """
    Получить все книги из базы данных
    """
    books_list = []
    books_ref = db.collection("books")
    for doc in books_ref.stream():
        book_data = doc.to_dict()
        # Конвертируем старый формат в новый если нужно
        authors = book_data.get("authors", [])
        if not authors and "author" in book_data:
            authors = [book_data["author"]]
            
        books_list.append({
            "id": doc.id,
            "title": book_data["title"],
            "authors": authors,
            "description": book_data.get("description", ""),
            "image_url": book_data.get("image_url", ""),
            "created_at": book_data.get("created_at", datetime.utcnow().isoformat()),
            "source": book_data.get("source", "manual"),
            "source_url": book_data.get("source_url"),
            "user_id": book_data.get("user_id", book_data.get("ownerId"))
        })
    return books_list

@router.get("/api/user/books")
def get_user_books(current_user: dict = Depends(get_current_user)):
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    books_list = []
    books_ref = db.collection("books")
    for b in books_ref.where("user_id", "==", current_user["_id"]).stream():
        book_data = b.to_dict()
        # Конвертируем старый формат в новый если нужно
        authors = book_data.get("authors", [])
        if not authors and "author" in book_data:
            authors = [book_data["author"]]
            
        books_list.append({
            "id": b.id,
            "title": book_data["title"],
            "authors": authors,
            "description": book_data.get("description", ""),
            "image_url": book_data.get("image_url", ""),
            "created_at": book_data.get("created_at", datetime.utcnow().isoformat()),
            "source": book_data.get("source", "manual"),
            "source_url": book_data.get("source_url"),
            "user_id": book_data.get("user_id", book_data.get("ownerId"))
        })
    return books_list

@router.post("/api/books", response_model=Book)
def create_book(book: CreateBookRequest, current_user: dict = Depends(get_current_user)):
    """
    Создать новую книгу
    
    Args:
        book: Данные книги
        current_user: Текущий пользователь
        
    Returns:
        Book: Созданная книга
    """
    if "_id" not in current_user:
        raise HTTPException(status_code=400, detail="Invalid user data.")
    
    book_id = str(uuid.uuid4())
    book_data = {
        "id": book_id,
        "title": book.title,
        "authors": book.authors,
        "description": book.description,
        "image_url": book.image_url,
        "user_id": current_user["_id"],
        "created_at": datetime.utcnow().isoformat(),
        "source": book.source,
        "source_url": book.source_url
    }
    
    books_ref = db.collection("books")
    books_ref.document(book_id).set(book_data)
    return Book(**book_data)

@router.delete("/api/books/{book_id}")
def delete_book(book_id: str):
    book_ref = db.collection("books").document(book_id)
    book = book_ref.get()
    if not book.exists:
        raise HTTPException(status_code=404, detail="Book not found.")
    book_ref.delete()
    return {"message": "Book deleted"}

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
    
    books_list = []
    shelf_books_ref = db.collection("shelf_books")
    books_ref = db.collection("books")
    
    for shelf_book in shelf_books_ref.where("shelfId", "==", shelf_id).stream():
        shelf_book_data = shelf_book.to_dict()
        book = books_ref.document(shelf_book_data["bookId"]).get()
        if book.exists:
            book_data = book.to_dict()
            # Конвертируем старый формат в новый если нужно
            authors = book_data.get("authors", [])
            if not authors and "author" in book_data:
                authors = [book_data["author"]]
                
            books_list.append({
                "id": book.id,
                "title": book_data["title"],
                "authors": authors,
                "description": book_data.get("description", ""),
                "image_url": book_data.get("image_url", ""),
                "created_at": book_data.get("created_at", datetime.utcnow().isoformat()),
                "source": book_data.get("source", "manual"),
                "source_url": book_data.get("source_url"),
                "user_id": book_data.get("user_id", book_data.get("ownerId"))
            })
    
    return books_list

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
    user_id = book_data.get("user_id", book_data.get("ownerId"))
    if user_id != current_user["_id"]:
        raise HTTPException(status_code=403, detail="You can only add your own books to the shelf.")
    
    # Add the book to the shelf
    shelf_book_id = str(uuid.uuid4())
    shelf_book_data = {
        "id": shelf_book_id,
        "shelfId": shelf_id,
        "bookId": book_id,
        "user_id": current_user["_id"],
        "created_at": datetime.utcnow().isoformat()
    }
    
    books_ref = db.collection("shelf_books")
    books_ref.document(shelf_book_id).set(shelf_book_data)
    return shelf_book_data

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

