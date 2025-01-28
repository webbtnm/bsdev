from pydantic import BaseModel, HttpUrl
from typing import List

# Book models
class CreateBookRequest(BaseModel):
    title: str
    authors: List[str]
    description: str | None = None
    image_url: str | None = None
    source: str = "manual"
    source_url: str | None = None

class Book(BaseModel):
    id: str
    title: str
    authors: List[str]
    description: str | None = None
    image_url: str | None = None
    user_id: str
    created_at: str
    source: str
    source_url: str | None = None

class LitresUrlInput(BaseModel):
    url: HttpUrl

class Author(BaseModel):
    name: str

class LitresBookResponse(BaseModel):
    title: str
    authors: List[str]
    description: str
    image_url: str

# User models
class UserOut(BaseModel):
    id: str
    username: str
    telegram_contact: str | None = None

# Shelf models
class Shelf(BaseModel):
    name: str
    description: str | None = None
    public: bool = True

class ShelfResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    public: bool
    ownerId: str

class ShelfMember(BaseModel):
    id: str
    shelfId: str
    userId: str 