from fastapi import APIRouter, HTTPException, Depends
from server.fastapi_auth import get_current_user
from db.firestore import db
from pydantic import BaseModel

router = APIRouter()

class Book(BaseModel):
    title: str
    author: str
    description: str | None = None

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