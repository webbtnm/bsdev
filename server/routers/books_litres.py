from bs4 import BeautifulSoup
import httpx
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query, Depends
from google.cloud import firestore
from datetime import datetime
import uuid
from server.fastapi_auth import get_current_user
import os

router = APIRouter()

# Инициализация Firestore с сервисным аккаунтом
credentials_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                              'webbshelf-firebase-adminsdk-pplzd-c166514851.json')
db = firestore.Client.from_service_account_json(credentials_path)

class BookDetails(BaseModel):
    title: str
    authors: List[str]
    description: str
    image_url: str

class SavedBook(BaseModel):
    id: str
    title: str
    authors: List[str]
    description: str
    image_url: str
    user_id: str
    created_at: str
    source_url: str
    source: str = "litres"

async def parse_book_details(html: str) -> BookDetails:
    soup = BeautifulSoup(html, 'lxml')
    
    # Получаем заголовок
    title_elem = soup.select_one('h1[itemprop="name"]')
    title = title_elem.text.strip() if title_elem else ""
    
    # Получаем авторов
    authors = []
    author_elems = soup.select('a[data-testid="art__personName--link"] span[itemprop="name"]')
    for author in author_elems:
        authors.append(author.text.strip())
    
    # Получаем описание
    description = ""
    desc_elem = soup.select_one('div.Truncate_truncated__jKdVt')
    if desc_elem:
        paragraphs = desc_elem.select('p')
        description = ' '.join(p.text.strip() for p in paragraphs)
    
    # Получаем URL изображения
    image_url = ""
    img_elem = soup.select_one('img[itemprop="image"]')
    if img_elem and 'src' in img_elem.attrs:
        image_url = img_elem['src']
        # Преобразуем относительный URL в абсолютный если нужно
        if image_url.startswith('./'):
            image_url = image_url.replace('./', 'https://www.litres.ru/')
    
    return BookDetails(
        title=title,
        authors=authors,
        description=description,
        image_url=image_url
    )

async def get_book_details(url: str) -> Optional[BookDetails]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return await parse_book_details(response.text)
    except Exception as e:
        print(f"Error fetching book details: {e}")
        return None

@router.get("/api/bookslitres")
async def parse_litres_book(url: str = Query(..., description="URL страницы книги на Litres")):
    """
    Парсит информацию о книге с сайта Litres по URL
    
    Args:
        url: URL страницы книги на Litres
        
    Returns:
        BookDetails: Информация о книге (заголовок, авторы, описание, URL обложки)
        
    Raises:
        HTTPException: Если не удалось получить или распарсить информацию о книге
    """
    if not url or not url.startswith("https://www.litres.ru/"):
        raise HTTPException(status_code=400, detail="Invalid Litres URL")
        
    book_details = await get_book_details(url)
    if not book_details:
        raise HTTPException(status_code=500, detail="Failed to parse book details")
        
    return book_details

@router.post("/api/bookslitres/save")
async def save_litres_book(
    url: str = Query(..., description="URL страницы книги на Litres"),
    current_user: dict = Depends(get_current_user)
):
    """
    Парсит и сохраняет книгу с Litres в библиотеку пользователя
    
    Args:
        url: URL страницы книги на Litres
        current_user: Текущий авторизованный пользователь
        
    Returns:
        SavedBook: Сохраненная информация о книге
        
    Raises:
        HTTPException: Если не удалось получить, распарсить или сохранить информацию о книге
    """
    if not url or not url.startswith("https://www.litres.ru/"):
        raise HTTPException(status_code=400, detail="Invalid Litres URL")
    
    # Проверяем структуру current_user
    print("Current user data:", current_user)
    print("Current user keys:", current_user.keys() if current_user else None)
    
    if not current_user:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # Получаем user_id из структуры current_user
    try:
        # Пробуем разные варианты получения ID
        user_id = None
        if isinstance(current_user, dict):
            user_id = (current_user.get('uid') or 
                      current_user.get('id') or 
                      current_user.get('user_id') or 
                      current_user.get('sub') or
                      (current_user.get('firebase_user', {}) or {}).get('uid') or
                      (current_user.get('user', {}) or {}).get('uid') or
                      current_user.get('_id'))
        
        print("Found user_id:", user_id)
        
        if not user_id:
            print("Available fields in current_user:", current_user)
            raise ValueError("No user ID found in any expected field")
            
    except Exception as e:
        print(f"Error getting user ID. Current user structure: {current_user}")
        raise HTTPException(status_code=500, detail=f"Unable to determine user ID: {str(e)}")
    
    # Получаем информацию о книге
    book_details = await get_book_details(url)
    if not book_details:
        raise HTTPException(status_code=500, detail="Failed to parse book details")
    
    # Создаем документ книги
    book_id = str(uuid.uuid4())
    book_data = {
        'id': book_id,
        'title': book_details.title,
        'authors': book_details.authors,
        'description': book_details.description,
        'image_url': book_details.image_url,
        'user_id': user_id,
        'created_at': datetime.utcnow().isoformat(),
        'source_url': url,
        'source': 'litres'
    }
    
    # Сохраняем в Firestore
    books_ref = db.collection('books')
    try:
        books_ref.document(book_id).set(book_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save book: {str(e)}")
    
    return SavedBook(**book_data) 