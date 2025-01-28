from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routers import books, users, shelves, books_litres
from server.fastapi_auth import router as auth_router

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Корневой маршрут
@app.get("/")
def read_root():
    return {"message": "Welcome to WebShelf API"}

# Включаем роутеры
app.include_router(books.router)
app.include_router(users.router)
app.include_router(shelves.router)
app.include_router(books_litres.router)
app.include_router(auth_router)  # Include auth router so /api/token and others are available

# Запуск приложения
# uvicorn server.fastapi_app:app --reload